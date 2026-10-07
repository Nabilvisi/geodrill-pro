"""Ownership, immutable dependencies and connected archive recovery."""
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from services.api import auth, access
from services.api.storage import canonical, digest, RevisionConflict
from packages.domain.wellbore_revisions import SurveySave

import pytest
from fastapi.testclient import TestClient
from services.api.main import create_app
from services.api.storage import Store
from services.application.wellbore_revisions import WellboreRevisionService

H = {'x-geodrill-client': 'workstation'}


@pytest.fixture
def env(tmp_path):
    app = create_app(data_dir=tmp_path / 'source', mode='local')
    with TestClient(app) as client:
        client.get('/api/session')
        project = client.post('/api/v1/projects', headers=H, json={'name':'Revision research', 'datum':'MSL', 'north_reference':'true'}).json()
        well = client.post(f"/api/v1/projects/{project['id']}/wells", headers=H, json={'name':'Research well'}).json()
        wb = client.post(f"/api/v1/wells/{well['id']}/wellbores", headers=H, json={'name':'Main'}).json()
        offset = client.post(f"/api/v1/wells/{well['id']}/wellbores", headers=H, json={'name':'Offset'}).json()
        yield client, app.state.store, project, wb, offset


def survey(client, wb, *, role='planned', base=None, east=0., inc=.2):
    body = {'trajectory_type':role, 'base_revision_id':base, 'change_note':'Synthetic revision', 'frame':{'datum':'MSL','north_reference':'true','coordinate_reference':'Declared synthetic local frame','wellhead_north_m':0.,'wellhead_east_m':east,'wellhead_elevation_m':25.}, 'evidence_state':'synthetic', 'survey_quality_note':'Synthetic input, no field qualification', 'survey':{'stations':[{'md_m':0.,'inclination_rad':0.,'azimuth_rad':0.},{'md_m':500.,'inclination_rad':inc,'azimuth_rad':.5},{'md_m':1000.,'inclination_rad':inc,'azimuth_rad':.5}]}}
    return client.post(f"/api/v1/wellbores/{wb['id']}/surveys", headers=H, json=body)


def trajectory(client, wb, source, base=None):
    r = client.post(f"/api/v1/wellbores/{wb['id']}/trajectories", headers=H, json={'survey_revision_id':source['id'], 'base_revision_id':base, 'change_note':'Calculate saved geometry'})
    assert r.status_code == 201, r.text
    return r.json()


def test_roles_are_independent_and_conflicts_do_not_replace_evidence(env):
    client, store, project, wb, offset = env
    p=survey(client,wb); assert p.status_code==201,p.text
    planned=p.json(); actual=survey(client,wb,role='actual').json()
    a=trajectory(client,wb,planned); b=trajectory(client,wb,actual)
    assert a['id']!=b['id'] and a['revision_no']==b['revision_no']==1
    assert survey(client,wb).status_code==409
    assert survey(client,offset).status_code==201
    new=survey(client,wb,base=planned['id'],inc=.3).json()
    historical=client.get(f"/api/v1/wellbores/{wb['id']}/revisions/{a['id']}").json()
    assert historical['revision']==a and historical['freshness']['stale']
    assert client.get(f"/api/v1/wellbores/{wb['id']}/directional-context?trajectory_type=actual").json()['active']['survey']['id']==actual['id']
    assert client.get(f"/api/v1/wellbores/{wb['id']}/directional-context").json()['active']['survey']['id']==new['id']
    assert store.audit_history()['integrity']=='verified'
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError,match='immutable'):
            db.execute('UPDATE wellbore_revisions SET sha256=? WHERE id=?',('0'*64,planned['id']))


def test_cross_wellbore_source_is_rejected_and_geometry_listing_is_scoped(env):
    client, store, project, wb, offset=env
    source=survey(client,wb).json(); t=trajectory(client,wb,source)
    r=client.post(f"/api/v1/wellbores/{offset['id']}/trajectories",headers=H,json={'survey_revision_id':source['id'],'change_note':'Foreign revision'})
    assert r.status_code==404
    assert client.get(f"/api/projects/{project['id']}/engineering-revisions?module=M1").json()==[]
    assert client.get(f"/api/projects/{project['id']}/engineering-revisions?module=M1&wellbore_id={wb['id']}&trajectory_type=planned").json()[0]['id']==t['id']


def test_withheld_uncertainty_and_offset_staleness_survive_reports_and_recovery(env,tmp_path):
    client, store, project, wb, offset=env
    source=survey(client,wb).json(); other=survey(client,offset,east=100.).json()
    t=trajectory(client,wb,source); ot=trajectory(client,offset,other)
    root=f"/api/v1/wellbores/{wb['id']}"
    u=client.post(root+'/uncertainty',headers=H,json={'trajectory_revision_id':t['id']})
    assert u.status_code==201,u.text
    assert u.json()['envelope']['status']=='withheld'
    p=client.post(root+'/anticollision/calculate',headers=H,json={'trajectory_revision_id':t['id'],'offset_wellbore_id':offset['id'],'offset_trajectory_revision_id':ot['id'],'correlation_mode':'independent'})
    assert p.status_code==201,p.text
    assert p.json()['envelope']['result']['clearance_generated'] is False
    initial_report=store.report(project['id'],store.create_report(project['id'])['id'])
    survey(client,offset,base=other['id'],east=105.)
    svc=WellboreRevisionService(store)
    assert svc.freshness(p.json())['stale']
    saved_report=store.report(project['id'],store.create_report(project['id'])['id'])
    assert saved_report['snapshot']['wellbore_state']['dependency_state'][p.json()['id']]['stale']
    raw=store.export_bundle(project['id'])
    destination=Store(tmp_path/'restored'); destination.restore_bundle(raw)
    restored=WellboreRevisionService(destination)
    assert restored.get(wb['id'],p.json()['id'])==p.json()
    assert restored.freshness(p.json())['stale']
    assert destination.calculations(project['id'])==store.calculations(project['id'])
    assert destination.report(project['id'],initial_report['snapshot']['id'])==initial_report
    assert destination.audit_history()['integrity']=='verified'


def test_original_raw_source_tampering_blocks_reopen(env):
    client, store, project, wb, offset=env
    source=survey(client,wb).json(); t=trajectory(client,wb,source)
    (store.root/'raw'/source['source_sha256']).write_bytes(b'changed')
    r=client.get(f"/api/v1/wellbores/{wb['id']}/revisions/{t['id']}")
    assert r.status_code==422 and 'integrity' in r.text.lower()


def test_explicit_csv_import_and_adoption_preserve_original_bytes(env):
    client,store,project,wb,offset=env
    draft=survey(client,wb).json()
    metadata={k:draft[k] for k in ('trajectory_type','change_note','frame','evidence_state','survey_quality_note','tool_metadata')}
    metadata.update(trajectory_type='actual',base_revision_id=None,evidence_state='unqualified_observation')
    raw=b'md[m],inclination[deg],azimuth[deg]\r\n0,0,0\r\n100,20,40\r\n'
    result=client.post(f"/api/v1/wellbores/{wb['id']}/surveys/import",headers=H,data={'metadata':json.dumps(metadata)},files={'file':('observed.csv',raw,'text/csv')})
    assert result.status_code==201,result.text
    source=result.json();assert (store.root/'raw'/source['source_sha256']).read_bytes()==raw
    assert source['evidence_state']=='unqualified_observation'
    adopted=client.post(f"/api/v1/wellbores/{offset['id']}/surveys/from-dataset",headers=H,json={**metadata,'dataset_id':source['dataset_id']})
    assert adopted.status_code==201,adopted.text
    assert adopted.json()['wellbore_id']==offset['id'] and adopted.json()['source_sha256']==source['source_sha256']


def test_simultaneous_save_has_one_winner_and_one_conflict(env):
    client,store,project,wb,offset=env
    source=survey(client,wb).json();svc=WellboreRevisionService(store)
    command=SurveySave.model_validate({k:source[k] for k in ('trajectory_type','change_note','frame','evidence_state','survey_quality_note','tool_metadata')}|{'base_revision_id':source['id']})
    def save():
        try:return svc.save_survey(wb['id'],command,source['dataset_id'])['id']
        except RevisionConflict:return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:save(),range(2)))
    assert results.count('conflict')==1 and len(svc.records(wb['id'],'survey'))==2


def test_engineering_case_freshness_is_an_overlay_and_scope_is_enforced(env):
    client,store,project,wb,offset=env
    source=survey(client,wb).json(); t=trajectory(client,wb,source)
    calc=store.calculation(project['id'],'test-bound',{'geometry_revision_id':t['id']},{'status':'withheld','equipment_control':False})
    frozen=canonical(calc)
    assert calc['wellbore_id']==wb['id']
    trajectory(client,wb,source,base=t['id'])
    states=client.get(f"/api/projects/{project['id']}/calculation-dependencies").json()
    assert states[calc['id']]['stale']
    assert canonical(next(c for c in store.calculations(project['id']) if c['id']==calc['id']))==frozen
    r=client.get(f"/api/projects/{project['id']}/geometry/{t['id']}",headers={'X-Geodrill-Wellbore':offset['id'],'X-Geodrill-Trajectory-Type':'planned'})
    assert r.status_code==422


def test_whole_workstation_recovery_and_restart_preserve_heads(env,tmp_path):
    from tools.backup_restore import backup_workstation,restore_workstation
    client,store,project,wb,offset=env
    source=survey(client,wb,role='scenario').json();t=trajectory(client,wb,source)
    archive=tmp_path/'whole.zip';saved=backup_workstation(store.root,archive)
    restore_workstation(archive,tmp_path/'whole-restored',saved['sha256'])
    restored=Store(tmp_path/'whole-restored')
    assert WellboreRevisionService(restored).head(wb['id'],'trajectory','scenario')==t
    assert restored.audit_history()==store.audit_history()
    restarted=Store(store.root)
    assert WellboreRevisionService(restarted).head(wb['id'],'survey','scenario')==source


@pytest.mark.parametrize('damage',['initial-base','missing-dependency','foreign-parent'])
def test_archive_semantic_tampering_rejected_even_with_matching_entry_hash(env,damage):
    from services.api.wellbore_archive import read_hierarchy,validate_hierarchy
    client,store,project,wb,offset=env
    source=survey(client,wb).json();trajectory(client,wb,source)
    with store.connect() as db:
        value=read_hierarchy(db,project['id'])
        datasets=[dict(r) for r in db.execute('SELECT * FROM datasets WHERE project_id=?',(project['id'],))]
        revisions=[dict(r) for r in db.execute('SELECT * FROM engineering_revisions WHERE project_id=?',(project['id'],))]
    row=value['wellbore_revisions'][0 if damage=='initial-base' else 1]
    payload=json.loads(row['payload'])
    if damage=='initial-base':row['base_revision_id']='missing';payload['base_revision_id']='missing'
    elif damage=='missing-dependency':payload['dependencies']=[]
    else:row['wellbore_id']='foreign';payload['wellbore_id']='foreign'
    row['payload']=canonical(payload);row['sha256']=digest(row['payload'].encode())
    for r in revisions:
        if r['id']==row['id']:r.update(payload=row['payload'],sha256=row['sha256'])
    with pytest.raises(ValueError):validate_hierarchy(value,project['id'],datasets,revisions)


def test_team_membership_hides_owned_revisions_and_blocks_viewer_writes(tmp_path):
    app=create_app(tmp_path/'team',mode='team');store=app.state.store
    admin=auth.create_user(store,'admin','Admin','admin','Synthetic-password-123!')
    viewer=auth.create_user(store,'viewer','Viewer','viewer','Synthetic-password-123!')
    outsider=auth.create_user(store,'other','Other','engineer','Synthetic-password-123!')
    from services.application.wells import WellService
    project=store.create_project({'name':'Private synthetic','datum':'MSL','north_reference':'true'})
    svc=WellService(store);well=svc.create_well(project['id'],'Private well');wb=svc.create_wellbore(well['id'],'Private bore')
    access.add_member(store,project['id'],viewer['id'],admin)
    with TestClient(app) as client:
        token=client.post('/api/team/login',json={'username':'other','password':'Synthetic-password-123!'}).json()['token']
        assert client.get(f"/api/v1/wellbores/{wb['id']}/directional-context",headers={'Authorization':'Bearer '+token}).status_code==404
        token=client.post('/api/team/login',json={'username':'viewer','password':'Synthetic-password-123!'}).json()['token']
        client.headers.update({'Authorization':'Bearer '+token})
        assert client.get(f"/api/v1/wellbores/{wb['id']}/directional-context").status_code==200
        assert survey(client,wb).status_code==403


def test_proximity_refuses_unimplemented_correlated_covariance(env):
    client,store,project,wb,offset=env
    t=trajectory(client,wb,survey(client,wb).json());ot=trajectory(client,offset,survey(client,offset,east=100).json())
    result=client.post(f"/api/v1/wellbores/{wb['id']}/anticollision/calculate",headers=H,json={'trajectory_revision_id':t['id'],'offset_wellbore_id':offset['id'],'offset_trajectory_revision_id':ot['id'],'correlation_mode':'systematic_geomagnetic','geomagnetic':{'b_total_nt':50000,'dip_deg':60}})
    assert result.status_code==422 and 'not implemented' in result.text
