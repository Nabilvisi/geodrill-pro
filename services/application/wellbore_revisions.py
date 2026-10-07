"""Immutable wellbore source revisions and saved directional workflows.

Kernel results stay authoritative. Legacy project sources are adopted only by an
explicit command; derived freshness never rewrites historical result bytes.
"""
import json
import math
from uuid import uuid4
from packages.domain.wellbore_revisions import SurveySave, SurveyFrame, TrajectorySave
from packages.domain.models import SurveyStation, TrajectoryType
from packages.engineering.models import SurveyRequest
from packages.engineering.geometry import GeometryInput, geometry_result
from packages.engineering.ingestion import survey_csv
from services.api.storage import Store, RevisionConflict, canonical, digest, now, current_actor
from services.application.wells import WellService
from services.application.directional import DirectionalService


class WellboreRevisionService:
    def __init__(self, store: Store):
        self.store = store
        self.wells = WellService(store)

    def scope(self, wellbore_id):
        wb = self.wells.get_wellbore(wellbore_id)
        well = self.wells.get_well(wb['well_id'])
        return wb, well, self.store.project(well['project_id'])

    @staticmethod
    def _checked(row):
        if digest(row['payload'].encode()) != row['sha256']:
            raise ValueError('Wellbore revision integrity check failed.')
        value = json.loads(row['payload'])
        for key in ('id', 'project_id', 'wellbore_id', 'kind', 'trajectory_type', 'revision_no', 'base_revision_id', 'created_at'):
            if value.get(key) != row[key]:
                raise ValueError('Wellbore revision ownership differs from preserved payload.')
        return {**value, 'sha256': row['sha256']}

    def records(self, wellbore_id, kind=None, trajectory_type=None):
        self.scope(wellbore_id)
        with self.store.connect() as db:
            rows = db.execute('SELECT * FROM wellbore_revisions WHERE wellbore_id=? AND (? IS NULL OR kind=?) AND (? IS NULL OR trajectory_type=?) ORDER BY revision_no DESC, rowid DESC', (wellbore_id, kind, kind, trajectory_type, trajectory_type)).fetchall()
        return [self._checked(r) for r in rows]

    def get(self, wellbore_id, revision_id, kind=None):
        self.scope(wellbore_id)
        with self.store.connect() as db:
            row = db.execute('SELECT * FROM wellbore_revisions WHERE wellbore_id=? AND id=?', (wellbore_id, revision_id)).fetchone()
        if row is None or (kind and row['kind'] != kind):
            raise KeyError('Revision not found in this wellbore.')
        value = self._checked(row)
        if value['kind'] == 'survey':
            source = self.store.dataset(value['project_id'], value['dataset_id'])
            normalized=SurveyRequest(stations=[{k:r[k] for k in ('md_m','inclination_rad','azimuth_rad')} for r in source['rows']])
            if normalized != SurveyRequest.model_validate(value['survey']):
                raise ValueError('Survey revision stations differ from preserved normalized source.')
            if source['source_hash'] != value['source_sha256']:
                raise ValueError('Survey source differs from its immutable revision.')
            raw = self.store.root / 'raw' / source['source_hash']
            if not raw.is_file() or digest(raw.read_bytes()) != value['source_sha256']:
                raise ValueError('Original survey source integrity check failed.')
        elif value['kind'] == 'trajectory':
            self.get(wellbore_id, value['survey_revision_id'], 'survey')
            geometry = self.store.revision(value['project_id'], revision_id)
            if geometry['sha256'] != value['sha256']:
                raise ValueError('Saved trajectory and engineering geometry differ.')
        else:
            self.get(wellbore_id,value['trajectory_revision_id'],'trajectory')
            if value['kind']=='proximity':
                self.get(value['offset_wellbore_id'],value['offset_trajectory_revision_id'],'trajectory')
        return value

    @staticmethod
    def _head(db, wellbore_id, kind, role):
        return db.execute('SELECT id,revision_no FROM wellbore_revisions WHERE wellbore_id=? AND kind=? AND trajectory_type=? ORDER BY revision_no DESC LIMIT 1', (wellbore_id, kind, role)).fetchone()

    def head(self, wellbore_id, kind, role):
        with self.store.connect() as db:
            row = self._head(db, wellbore_id, kind, role)
        return self.get(wellbore_id, row['id'], kind) if row else None

    def check_base(self, wellbore_id, kind, role, expected):
        with self.store.connect() as db:
            current = self._head(db, wellbore_id, kind, role)
        if (current['id'] if current else None) != expected:
            raise RevisionConflict('This wellbore revision changed. Reload before saving.')

    def _append(self, wellbore_id, kind, role, expected, content, *, record_id=None, envelope=None):
        _, _, project = self.scope(wellbore_id)
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            head = self._head(db, wellbore_id, kind, role)
            if (head['id'] if head else None) != expected:
                raise RevisionConflict('This wellbore revision changed. Reload before saving.')
            value = {**content, 'id': record_id or str(uuid4()), 'project_id': project['id'], 'wellbore_id': wellbore_id, 'kind': kind, 'trajectory_type': role, 'revision_no': (head['revision_no']+1 if head else 1), 'base_revision_id': expected, 'created_at': now(), 'created_by': current_actor.get()}
            encoded = canonical(value); sha = digest(encoded.encode())
            db.execute('INSERT INTO wellbore_revisions VALUES(?,?,?,?,?,?,?,?,?,?)', (value['id'], project['id'], wellbore_id, kind, role, value['revision_no'], expected, encoded, sha, value['created_at']))
            if kind == 'trajectory':
                db.execute('INSERT INTO engineering_revisions VALUES(?,?,?,?,?,?)', (value['id'], project['id'], 'M1', encoded, sha, value['created_at']))
            if envelope:
                calc = {'id': envelope['calculation_id'], 'model': envelope['model'], 'inputs_si': value.get('calculation_inputs', {}), 'result': envelope['result'], 'created_at': value['created_at'], 'envelope': envelope, 'wellbore_revision_id': value['id'], 'wellbore_id': wellbore_id}
                db.execute('INSERT INTO calculations VALUES(?,?,?,?)', (calc['id'], project['id'], canonical(calc), calc['created_at']))
                self.store.audit(db, 'calculation.executed', project['id'], calc)
            self.store.audit(db, 'wellbore.revised', project['id'], {'revision_id': value['id'], 'wellbore_id': wellbore_id, 'kind': kind, 'trajectory_type': role, 'sha256': sha, 'base_revision_id': expected})
        return self.get(wellbore_id, value['id'])

    def _validate_frame(self, project, command: SurveySave):
        if command.frame.datum != project['datum'] or command.frame.north_reference != project['north_reference']:
            raise ValueError('Survey datum and north reference must match the project.')
        if command.trajectory_type == 'actual' and command.evidence_state == 'authored_design':
            raise ValueError('An authored design cannot be labelled actual observations.')

    def save_survey(self, wellbore_id, command: SurveySave, dataset_id):
        _, _, project = self.scope(wellbore_id)
        self._validate_frame(project, command)
        source = self.store.dataset(project['id'], dataset_id)
        if source['kind'] != 'survey':
            raise ValueError('A survey source is required.')
        survey = SurveyRequest(stations=[{k: r[k] for k in ('md_m', 'inclination_rad', 'azimuth_rad')} for r in source['rows']])
        return self._append(wellbore_id, 'survey', command.trajectory_type, command.base_revision_id, {'dataset_id': dataset_id, 'source_sha256': source['source_hash'], 'filename': source['filename'], 'survey': survey.model_dump(), 'frame': command.frame.model_dump(), 'evidence_state': command.evidence_state, 'survey_quality_note': command.survey_quality_note, 'tool_metadata': command.tool_metadata, 'change_note': command.change_note, 'dependencies': []})

    def import_survey(self, wellbore_id, command, filename, raw, *, authored=False):
        _, _, project = self.scope(wellbore_id)
        self._validate_frame(project, command)
        self.check_base(wellbore_id, 'survey', command.trajectory_type, command.base_revision_id)
        if authored:
            from packages.engineering.physics import minimum_curvature
            rows = minimum_curvature(command.survey)
        else:
            rows = survey_csv(raw.decode('utf-8-sig'))
        source = self.store.import_data(project['id'], 'survey', filename, raw, rows, {'datum': project['datum'], 'north_reference': project['north_reference'], 'model': 'minimum-curvature', 'model_version': '0.1.0', 'uncertainty': 'not evaluated', 'source_origin': 'authored design' if authored else 'imported observations'}, [])
        return self.save_survey(wellbore_id, command, source['id'])

    def save_trajectory(self, wellbore_id, command: TrajectorySave):
        source = self.get(wellbore_id, command.survey_revision_id, 'survey')
        frame = source['frame']; role = source['trajectory_type']
        self.check_base(wellbore_id, 'trajectory', role, command.base_revision_id)
        geometry = command.geometry or GeometryInput(survey_dataset_id=source['dataset_id'], **{k:v for k,v in frame.items() if k != 'north_reference'}, survey_quality_note=source['survey_quality_note'], tool_to_bit_offset_m=0.)
        if geometry.survey_dataset_id != source['dataset_id'] or any(getattr(geometry,k) != v for k,v in frame.items() if k != 'north_reference'):
            raise ValueError('Geometry must retain its survey revision source and declared frame.')
        survey = SurveyRequest.model_validate(source['survey'])
        rows = [SurveyStation(md_m=s.md_m, inc_rad=s.inclination_rad, azi_rad=s.azimuth_rad, tool_code=str(source['tool_metadata'].get('tool_code','undeclared'))) for s in survey.stations]
        old = self.head(wellbore_id, 'trajectory', role)
        trajectory, envelope = DirectionalService.calculate_minimum_curvature_trajectory(rows, wellbore_id, source['id'], (old['revision_no']+1 if old else 1), TrajectoryType(role))
        result = geometry_result(geometry, survey)
        result.update(survey_source_sha256=source['source_sha256'], survey_filename=source['filename'], north_reference=frame['north_reference'])
        env = envelope.model_dump(mode='json'); env['result'].update(equipment_control=False, equipment_authority='none', clearance_generated=False)
        dep = [{'wellbore_id': wellbore_id, 'kind': 'survey', 'trajectory_type': role, 'revision_id': source['id']}]
        return self._append(wellbore_id, 'trajectory', role, command.base_revision_id, {'module':'M1','input':geometry.model_dump(), 'result':result, 'trajectory':trajectory.model_dump(mode='json'), 'survey_revision_id':source['id'], 'frame':frame, 'evidence_state':source['evidence_state'], 'change_note':command.change_note, 'dependencies':dep, 'envelope':env, 'calculation_inputs':{'survey':source['survey'],'frame':frame,'survey_revision_id':source['id']}}, record_id=trajectory.id, envelope=env)

    @staticmethod
    def _stations(source):
        return [{'md_m': s['md_m'], 'inclination_deg': math.degrees(s['inclination_rad']), 'azimuth_deg':math.degrees(s['azimuth_rad'])} for s in source['survey']['stations']]

    def save_uncertainty(self, wellbore_id, command):
        trajectory = self.get(wellbore_id, command.trajectory_revision_id, 'trajectory')
        source = self.get(wellbore_id, trajectory['survey_revision_id'], 'survey')
        forbidden = {'stations', 'datum', 'elevation_m', 'north_reference', 'source_label'} & command.metadata.keys()
        if forbidden:
            raise ValueError('Uncertainty station/frame/source bindings are supplied by the saved revision.')
        frame = source['frame']
        if frame['north_reference'] != 'true':
            raise ValueError('The pinned uncertainty adapter requires true-north observations; grid corrections must be declared and converted first.')
        payload = {**source['tool_metadata'], **command.metadata, 'stations':self._stations(source), 'datum':frame['datum'], 'elevation_m':frame['wellhead_elevation_m'], 'source_label':'iscwsa_calculated'}
        envelope = DirectionalService.calculate_uncertainty(payload, trajectory['id'], source['id']).model_dump(mode='json')
        role = trajectory['trajectory_type']; previous = self.head(wellbore_id,'uncertainty',role)
        dependencies = trajectory['dependencies']+[{'wellbore_id':wellbore_id,'kind':'trajectory','trajectory_type':role,'revision_id':trajectory['id']}]
        return self._append(wellbore_id,'uncertainty',role,previous['id'] if previous else None,{'envelope':envelope,'trajectory_revision_id':trajectory['id'],'survey_revision_id':source['id'],'calculation_inputs':payload,'dependencies':dependencies},envelope=envelope)

    def save_proximity(self, wellbore_id, command):
        reference = self.get(wellbore_id, command.trajectory_revision_id,'trajectory')
        if self.scope(command.offset_wellbore_id)[2]['id'] != reference['project_id']:
            raise KeyError('Offset revision not found in this project.')
        offset = self.get(command.offset_wellbore_id,command.offset_trajectory_revision_id,'trajectory')
        if reference['project_id'] != offset['project_id']:
            raise ValueError('Offset revisions must belong to the same project.')
        if wellbore_id == command.offset_wellbore_id:
            raise ValueError('Select a different offset wellbore.')
        for key in ('coordinate_reference','datum','north_reference'):
            if reference['frame'][key] != offset['frame'][key]:
                raise ValueError('Offset comparison requires an explicitly shared coordinate frame, datum and north reference.')
        a=self.get(wellbore_id,reference['survey_revision_id'],'survey'); b=self.get(command.offset_wellbore_id,offset['survey_revision_id'],'survey')
        def origin(t):
            f=t['frame'];return [f['wellhead_north_m'],f['wellhead_east_m'],-f['wellhead_elevation_m']]
        if (len(a['survey']['stations'])-1)*(len(b['survey']['stations'])-1)>100000:
            raise ValueError('This preview allows at most 100,000 segment pairs per offset calculation. Create an explicitly reviewed reduced source; no automatic resampling is performed.')
        if command.correlation_mode != 'independent':
            raise ValueError('Correlated covariance and separation-factor calculations are not implemented by this preserved proximity kernel. Only geometric distance with an explicitly independent assumption is available.')
        payload={'reference_well_name':self.scope(wellbore_id)[0]['name'],'offset_well_name':self.scope(command.offset_wellbore_id)[0]['name'],'reference_stations':self._stations(a),'offset_stations':self._stations(b),'reference_start_nev':origin(reference),'offset_start_nev':origin(offset),'geomagnetic':command.geomagnetic or None,'correlation_mode':command.correlation_mode}
        envelope=DirectionalService.calculate_anticollision(payload,reference['id']).model_dump(mode='json')
        envelope['result'].update(separation_withheld=True,separation_withholding_reason='The preserved proximity kernel computes segment geometry only. It does not propagate positional covariance or calculate a separation factor.',equipment_control=False,equipment_authority='none')
        envelope['survey_revision_id']=a['id']; role=reference['trajectory_type']; previous=self.head(wellbore_id,'proximity',role)
        dependencies=reference['dependencies']+offset['dependencies']+[{'wellbore_id':t['wellbore_id'],'kind':'trajectory','trajectory_type':t['trajectory_type'],'revision_id':t['id']} for t in (reference,offset)]
        return self._append(wellbore_id,'proximity',role,previous['id'] if previous else None,{'envelope':envelope,'trajectory_revision_id':reference['id'],'survey_revision_id':a['id'],'offset_wellbore_id':offset['wellbore_id'],'offset_trajectory_revision_id':offset['id'],'calculation_inputs':payload,'dependencies':dependencies},envelope=envelope)

    def freshness(self, value):
        reasons=[]
        for dependency in value.get('dependencies',[]):
            head=self.head(dependency['wellbore_id'],dependency['kind'],dependency['trajectory_type'])
            if not head or head['id'] != dependency['revision_id']:
                reasons.append(f"{dependency['kind']} changed in {dependency['wellbore_id']} ({dependency['trajectory_type']})")
        return {'stale':bool(reasons),'reasons':reasons}

    def context(self, wellbore_id, role):
        wb,well,project=self.scope(wellbore_id)
        values=self.records(wellbore_id)
        active={kind:self.head(wellbore_id,kind,role) for kind in ('survey','trajectory','uncertainty','proximity')}
        source=self.store.dataset(project['id'],active['survey']['dataset_id']) if active['survey'] else None
        comparisons={}
        for lane in ('planned','actual','scenario'):
            head=self.head(wellbore_id,'trajectory',lane)
            if head:comparisons[lane]={'revision_id':head['id'],'revision_no':head['revision_no'],**self.freshness(head)}
        return {'wellbore':wb,'well':well,'project_id':project['id'],'trajectory_type':role,'active':active,'survey_source':source,'comparison_state':comparisons,'revisions':[{k:v[k] for k in ('id','kind','trajectory_type','revision_no','created_at','sha256')} for v in values],'freshness':{k:self.freshness(v) for k,v in active.items() if v}}

    def calculation_freshness(self, project_id):
        """Overlay dependency state without modifying legacy calculation bytes."""
        states={}
        for calculation in self.store.calculations(project_id):
            if calculation.get('wellbore_revision_id'):
                record=self.get(calculation['wellbore_id'],calculation['wellbore_revision_id'])
                states[calculation['id']]=self.freshness(record)
                continue
            geometry_id=calculation['inputs_si'].get('geometry_revision_id')
            if not geometry_id:continue
            geometry=self.store.revision(project_id,geometry_id)
            if not geometry.get('wellbore_id'):continue
            record=self.get(geometry['wellbore_id'],geometry_id,'trajectory')
            state=self.freshness(record)
            head=self.head(record['wellbore_id'],'trajectory',record['trajectory_type'])
            if not head or head['id']!=record['id']:
                state['stale']=True;state['reasons'].append('A newer trajectory/geometry revision exists in this wellbore role.')
            states[calculation['id']]=state
        return states
