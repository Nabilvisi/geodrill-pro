"""Offset input provenance, numerical quantiles, saved evidence and authorization."""
import copy
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from services.api.main import create_app
from services.api.storage import Store, canonical, digest
from services.api import auth, programmes
from test_geometry_casing import api_setup
from packages.engineering.offset_benchmarking import OffsetBenchmarkingInput, calculate_offset_benchmarks


@pytest.fixture
def context(api_setup):
    client, project, base, geometry, store, root = api_setup
    response = client.post(base+'/geometry', json={'geometry':geometry,'change_note':'Synthetic offset workflow fixture'})
    assert response.status_code == 201, response.text
    revision=response.json()
    draft=client.get(base+'/research/offset-benchmarking/template/'+revision['id']).json()
    return client, project, base, store, root, revision, draft


def test_offset_import_save_search_report_restart_and_restore(context, tmp_path):
    c,p,b,store,root,rev,draft=context
    raw=json.dumps(draft,indent=2).encode()
    imported=c.post(b+'/research/offset-benchmarking/imports',files={'file':('synthetic-offsets.json',raw,'application/json')})
    assert imported.status_code==201,imported.text
    document=imported.json(); saved=c.post(b+'/calculations/offset-benchmarking',json=document['inputs_si'])
    assert saved.status_code==200,saved.text
    calc=saved.json();result=calc['result']
    assert result['status']=='calculated' and result['eligible_cohort_count']==3
    assert result['input_document_sha256']==hashlib.sha256(raw).hexdigest()
    assert result['input_document_matches_current'] is True
    assert result['geometry_sha256']==rev['sha256']
    assert result['approval_issued'] is False and result['equipment_authority']=='none'
    citations=c.get(b+'/evidence/search',params={'q':draft['study_name']}).json()['citations']
    citation=next(x for x in citations if x['entity_id']==calc['id'])
    assert citation['sha256_hash']==digest(canonical(calc).encode())
    assert citation['sha256_hash']!=rev['sha256']
    report=c.post(b+'/reports').json()
    snapshot=c.get(b+'/reports/'+report['id']).json()
    assert calc in snapshot['snapshot']['calculations']
    restart=TestClient(create_app(root));restart.get('/api/session')
    assert restart.get(b+'/calculations?model=offset-benchmarking').json()==[calc]
    fresh=Store(tmp_path/'restored');fresh.restore_bundle(store.export_bundle(p['id']))
    assert fresh.calculations(p['id'],'offset-benchmarking')==[calc]
    assert fresh.audit_history()['integrity']=='verified'


def test_offsets_quantiles_use_unrounded_duration_and_rig_rate(context):
    draft=copy.deepcopy(context[-1]);draft['planned_interval_m']=375.
    result=calculate_offset_benchmarks(OffsetBenchmarkingInput.model_validate(draft))
    # Native total hours are 50,60,70 per 1000 m. Linear quantiles: 52,60,68.
    assert result['projections']['projected_duration_days']=={'p10_favorable':.81,'p50_median':.94,'p90_conservative':1.06}
    assert result['projections']['rig_time_cost_scenario']['p50_median']==93750.
    assert result['projections']['projected_total_cost']['p50_median']==450000.
    draft['planned_rig_rate_per_day']=200000.
    changed=calculate_offset_benchmarks(OffsetBenchmarkingInput.model_validate(draft))
    assert changed['projections']['rig_time_cost_scenario']['p50_median']==187500.
    assert changed['projections']['projected_total_cost']==result['projections']['projected_total_cost']


def test_mixed_currency_excludes_records_and_withholds_small_cohort(context):
    draft=copy.deepcopy(context[-1]);draft['offset_wells'][1]['cost_currency']='IDR'
    result=calculate_offset_benchmarks(OffsetBenchmarkingInput.model_validate(draft))
    assert result['status']=='withheld' and result['eligible_cohort_count']==2
    assert 'currency' in result['excluded_wells'][0]['reason'].lower()
    assert result['projections'] is None


def test_unknown_evidence_withholds_three_record_projection(context):
    draft=copy.deepcopy(context[-1]);draft['evidence_state']='unknown'
    result=calculate_offset_benchmarks(OffsetBenchmarkingInput.model_validate(draft))
    assert result['status']=='withheld' and result['eligible_cohort_count']==3
    assert result['projections'] is None and 'unknown' in result['reasons'][0]
    for field in ('drilling_hours', 'drilled_interval_m'):
        invalid=copy.deepcopy(draft);invalid['offset_wells'][0][field]=1e-300
        with pytest.raises(ValueError):
            OffsetBenchmarkingInput.model_validate(invalid)


def test_offset_edit_preserves_original_and_records_changed_evidence(context):
    c,p,b,store,root,rev,draft=context
    raw=json.dumps(draft).encode()
    document=c.post(b+'/research/offset-benchmarking/imports',files={'file':('offsets.json',raw)}).json()
    value=document['inputs_si'];value['planned_interval_m']=500.
    saved=c.post(b+'/calculations/offset-benchmarking',json=value)
    assert saved.status_code==200,saved.text
    assert saved.json()['result']['input_document_matches_current'] is False
    assert (root/'raw'/document['source_sha256']).read_bytes()==raw


@pytest.mark.parametrize('patch',[{'depth_datum':'MSL'},{'geometry_revision_id':'missing'},{'offset_wells':[]}])
def test_offset_bad_context_never_saves_calculation(context, patch):
    c,p,b,store,root,rev,draft=context;draft=copy.deepcopy(draft);draft.update(patch)
    response=c.post(b+'/calculations/offset-benchmarking',json=draft)
    assert response.status_code in (404,422)
    assert store.calculations(p['id'],'offset-benchmarking')==[]


def test_cross_project_geometry_and_document_denied(context):
    c,p,b,store,root,rev,draft=context
    other=c.post('/api/projects',json={'name':'Other','well_name':'Other','datum':'RKB','bit_diameter_m':.2,'origin':'synthetic'}).json()
    response=c.post('/api/projects/'+other['id']+'/calculations/offset-benchmarking',json=draft)
    assert response.status_code==404


def test_offsets_and_search_enforce_team_roles_and_membership(context):
    c,p,b,store,root,rev,draft=context
    viewer=auth.create_user(store,'viewer','Viewer','viewer','test correct horse battery',actor='test')
    engineer=auth.create_user(store,'engineer','Engineer','engineer','test correct horse battery',actor='test')
    from services.api.access import add_member
    add_member(store,p['id'],viewer['id'],'test')
    team=TestClient(create_app(root,mode='team'))
    vt,_=auth.login(store,'viewer','test correct horse battery')
    et,_=auth.login(store,'engineer','test correct horse battery')
    vh={'Authorization':'Bearer '+vt};eh={'Authorization':'Bearer '+et}
    assert team.get(b+'/evidence/search?q=fixture',headers=vh).status_code==200
    assert team.post(b+'/calculations/offset-benchmarking',json=draft,headers=vh).status_code==403
    assert team.get(b+'/evidence/search?q=fixture',headers=eh).status_code==404
    assert team.post(b+'/calculations/offset-benchmarking',json=draft,headers=eh).status_code==404


def test_programme_search_cites_actual_version_content(context):
    c,p,b,store,root,rev,draft=context
    author=auth.create_user(store,'author','Author','engineer','test correct horse battery',actor='test')
    prog=programmes.create_programme(store,p['id'],'Synthetic offset programme',{'interval_m':1000},author)
    response=c.get(b+'/evidence/search?q=programme').json()
    citation=next(x for x in response['citations'] if x['entity_id']==prog['id'])
    assert citation['revision_id']==prog['versions'][0]['id']
    assert citation['sha256_hash']==prog['versions'][0]['content_sha256']
    assert "status 'draft'" in citation['matched_snippet']
    assert c.get(b+'/programmes/'+prog['id']).json()==prog
    other=c.post('/api/projects',json={'name':'Other','well_name':'Other','datum':'RKB','bit_diameter_m':.2,'origin':'synthetic'}).json()
    assert c.get('/api/projects/'+other['id']+'/programmes/'+prog['id']).status_code==404
