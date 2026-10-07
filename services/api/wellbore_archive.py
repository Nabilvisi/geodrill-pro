"""Versioned hierarchy export/restore validation; no inferred ownership."""
import json
import re
from services.api.storage import canonical, digest
from packages.domain.models import FieldModel, Well, Wellbore, Target
from packages.domain.wellbore_revisions import SurveySave
from packages.engineering.models import SurveyRequest
from packages.engineering.geometry import GeometryInput
from packages.domain.calculation import CalculationEnvelope

COLUMNS={
 'fields':('id','project_id','name','payload','created_at'),
 'wells':('id','project_id','field_id','name','uwi','payload','created_at'),
 'wellbores':('id','well_id','name','uwi','sidetrack_parent_id','wellbore_type','payload','created_at'),
 'targets':('id','wellbore_id','name','geometry_type','payload','created_at'),
 'wellbore_revisions':('id','project_id','wellbore_id','kind','trajectory_type','revision_no','base_revision_id','payload','sha256','created_at')}


def read_hierarchy(db,project_id):
    queries={
      'fields':'SELECT * FROM fields WHERE project_id=? ORDER BY rowid',
      'wells':'SELECT * FROM wells WHERE project_id=? ORDER BY rowid',
      'wellbores':'SELECT b.* FROM wellbores b JOIN wells w ON w.id=b.well_id WHERE w.project_id=? ORDER BY b.rowid',
      'targets':'SELECT t.* FROM targets t JOIN wellbores b ON b.id=t.wellbore_id JOIN wells w ON w.id=b.well_id WHERE w.project_id=? ORDER BY t.rowid',
      'wellbore_revisions':'SELECT * FROM wellbore_revisions WHERE project_id=? ORDER BY rowid'}
    return {table:[dict(r) for r in db.execute(query,(project_id,))] for table,query in queries.items()}


def validate_hierarchy(value,project_id,datasets,revisions,normalized_sources=None,calculations=None):
    if not isinstance(value,dict) or set(value)!=set(COLUMNS):raise ValueError('Unsupported wellbore hierarchy archive fields.')
    maps={}
    for table,columns in COLUMNS.items():
        rows=value[table]
        if not isinstance(rows,list):raise ValueError('Invalid hierarchy records.')
        for row in rows:
            if not isinstance(row,dict) or set(row)!=set(columns) or not isinstance(row['id'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',row['id']):
                raise ValueError('Invalid hierarchy record fields or identity.')
            payload=json.loads(row['payload'])
            if not isinstance(payload,dict):raise ValueError('Invalid hierarchy payload.')
            models={'fields':FieldModel,'wells':Well,'wellbores':Wellbore,'targets':Target}
            if table in models:models[table].model_validate(payload)
            for key in columns:
                if key in {'payload','sha256','created_at'}:continue
                if key in payload and payload[key]!=row[key]:raise ValueError('Hierarchy record differs from its payload.')
            if 'project_id' in row and row['project_id']!=project_id:raise ValueError('Hierarchy belongs to a different project.')
        maps[table]={r['id']:r for r in rows}
        if len(maps[table])!=len(rows):raise ValueError('Duplicate hierarchy identity.')
    for row in value['wells']:
        if row['field_id'] is not None and row['field_id'] not in maps['fields']:raise ValueError('Foreign well field in hierarchy.')
    for row in value['wellbores']:
        if row['well_id'] not in maps['wells']:raise ValueError('Foreign wellbore parent in hierarchy.')
        seen={row['id']};parent=row['sidetrack_parent_id']
        while parent:
            if parent in seen or parent not in maps['wellbores'] or maps['wellbores'][parent]['well_id']!=row['well_id']:
                raise ValueError('Invalid or cyclic sidetrack parent in hierarchy.')
            seen.add(parent);parent=maps['wellbores'][parent]['sidetrack_parent_id']
    for row in value['targets']:
        if row['wellbore_id'] not in maps['wellbores']:raise ValueError('Foreign target parent in hierarchy.')
    source_map={r['id']:r for r in datasets};geometry_map={r['id']:r for r in revisions};numbers=set()
    for row in value['wellbore_revisions']:
        if row['wellbore_id'] not in maps['wellbores'] or row['kind'] not in {'survey','trajectory','uncertainty','proximity'} or row['trajectory_type'] not in {'planned','actual','scenario'} or type(row['revision_no']) is not int or row['revision_no']<1:
            raise ValueError('Invalid wellbore revision ownership or role.')
        key=(row['wellbore_id'],row['kind'],row['trajectory_type'],row['revision_no'])
        if key in numbers:raise ValueError('Duplicate revision number.')
        numbers.add(key)
        if digest(row['payload'].encode())!=row['sha256']:raise ValueError('Wellbore revision evidence hash mismatch.')
        payload=json.loads(row['payload'])
        for key in ('id','project_id','wellbore_id','kind','trajectory_type','revision_no','base_revision_id','created_at'):
            if payload.get(key)!=row[key]:raise ValueError('Wellbore revision envelope identity mismatch.')
        base=maps['wellbore_revisions'].get(row['base_revision_id'])
        if row['revision_no']==1:
            if row['base_revision_id'] is not None:raise ValueError('Initial revision cannot have a base.')
        elif not base or any(base[k]!=row[k] for k in ('wellbore_id','kind','trajectory_type')) or base['revision_no']!=row['revision_no']-1:
            raise ValueError('Wellbore revision base chain mismatch.')
        if row['kind']=='survey':
            dataset=source_map.get(payload.get('dataset_id'))
            if not dataset or dataset['kind']!='survey' or dataset['source_hash']!=payload.get('source_sha256'):raise ValueError('Survey revision source mismatch.')
            SurveySave.model_validate({k:payload[k] for k in ('trajectory_type','base_revision_id','change_note','frame','evidence_state','survey_quality_note','tool_metadata')})
            SurveyRequest.model_validate(payload['survey'])
            if normalized_sources is not None and SurveyRequest.model_validate(payload['survey']) != normalized_sources[payload['dataset_id']]:raise ValueError('Archived survey stations differ from preserved normalized source.')
            if row['trajectory_type']=='actual' and payload['evidence_state']=='authored_design':raise ValueError('An authored design cannot be restored as actual observations.')
            expected=[]
        elif row['kind']=='trajectory':
            geometry=geometry_map.get(row['id'])
            if not geometry or geometry['payload']!=row['payload'] or geometry['sha256']!=row['sha256']:raise ValueError('Trajectory/geometry archive mismatch.')
            source=maps['wellbore_revisions'].get(payload.get('survey_revision_id'))
            if not source or source['kind']!='survey' or source['wellbore_id']!=row['wellbore_id'] or source['trajectory_type']!=row['trajectory_type']:raise ValueError('Trajectory survey ownership mismatch.')
            source_payload=json.loads(source['payload']);g=GeometryInput.model_validate(payload['input'])
            if payload['frame']!=source_payload['frame'] or g.survey_dataset_id!=source_payload['dataset_id'] or any(getattr(g,k)!=v for k,v in payload['frame'].items() if k!='north_reference'):raise ValueError('Trajectory frame/source mismatch.')
            expected=[source]
        else:
            trajectory=maps['wellbore_revisions'].get(payload.get('trajectory_revision_id'))
            if not trajectory or trajectory['kind']!='trajectory' or trajectory['wellbore_id']!=row['wellbore_id'] or trajectory['trajectory_type']!=row['trajectory_type']:raise ValueError('Calculation trajectory ownership mismatch.')
            t=json.loads(trajectory['payload']);source=maps['wellbore_revisions'].get(payload.get('survey_revision_id'))
            if not source or source['id']!=t['survey_revision_id']:raise ValueError('Calculation survey dependency mismatch.')
            expected=[source,trajectory]
            if row['kind']=='proximity':
                offset=maps['wellbore_revisions'].get(payload.get('offset_trajectory_revision_id'))
                if not offset or offset['kind']!='trajectory' or offset['wellbore_id']!=payload.get('offset_wellbore_id') or offset['wellbore_id']==row['wellbore_id']:raise ValueError('Proximity offset ownership mismatch.')
                ot=json.loads(offset['payload'])
                if any(t['frame'][k]!=ot['frame'][k] for k in ('coordinate_reference','datum','north_reference')):raise ValueError('Proximity coordinate frame mismatch.')
                expected += [maps['wellbore_revisions'][ot['survey_revision_id']],offset]
        if row['kind']!='survey':
            envelope=CalculationEnvelope.model_validate(payload['envelope'])
            if envelope.geometry_revision_id!=(row['id'] if row['kind']=='trajectory' else payload['trajectory_revision_id']) or envelope.survey_revision_id!=payload['survey_revision_id']:raise ValueError('Calculation envelope dependency mismatch.')
            if calculations is not None:
                matching=next((json.loads(c['payload']) for c in calculations if c['id']==envelope.calculation_id),None)
                if not matching or matching.get('envelope')!=payload['envelope'] or matching.get('wellbore_revision_id')!=row['id'] or matching.get('wellbore_id')!=row['wellbore_id'] or matching['inputs_si']!=payload['calculation_inputs'] or matching['result']!=payload['envelope']['result']:raise ValueError('Saved calculation evidence differs from its owned revision.')
        deps=payload.get('dependencies')
        if not isinstance(deps,list) or len(deps)!=len(expected) or {d.get('revision_id') for d in deps}!={e['id'] for e in expected}:raise ValueError('Missing or duplicate revision dependency.')
        for dep in payload.get('dependencies',[]):
            referenced=maps['wellbore_revisions'].get(dep.get('revision_id'))
            if not referenced or any(dep.get(k)!=referenced[k] for k in ('wellbore_id','kind','trajectory_type')):raise ValueError('Foreign revision dependency in hierarchy.')
    return value


def restore_hierarchy(db,value):
    db.execute('PRAGMA defer_foreign_keys=ON')
    for table,columns in COLUMNS.items():
        for row in value[table]:
            if db.execute(f'SELECT 1 FROM {table} WHERE id=?',(row['id'],)).fetchone():raise ValueError('Hierarchy identity already exists in this workstation.')
            placeholders=','.join('?' for _ in columns)
            db.execute(f'INSERT INTO {table}({",".join(columns)}) VALUES({placeholders})',[row[c] for c in columns])


def report_hierarchy(store,project_id):
    from services.application.wellbore_revisions import WellboreRevisionService
    svc=WellboreRevisionService(store)
    with store.connect() as db:value=read_hierarchy(db,project_id)
    records=[svc.get(r['wellbore_id'],r['id']) for r in value['wellbore_revisions']]
    return {**{k:[json.loads(r['payload']) for r in value[k]] for k in ('fields','wells','wellbores','targets')},'revisions':records,'dependency_state':{r['id']:svc.freshness(r) for r in records},'calculation_dependency_state':svc.calculation_freshness(project_id)}
