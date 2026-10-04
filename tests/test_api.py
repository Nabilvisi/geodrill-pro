import hashlib
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient
from services.api.main import create_app
from services.api.storage import canonical
from services.api import demo

HEADERS = {'X-Geodrill-Client':'workstation'}


@pytest.fixture
def setup(tmp_path):
    app = create_app(tmp_path)
    client = TestClient(app)
    client.get('/api/session')
    client.headers.update(HEADERS)
    project = client.post('/api/demo').json()
    return client, project, app.state.store, tmp_path


def test_api_auth_origin_host_and_mutation_boundary(tmp_path):
    c = TestClient(create_app(tmp_path))
    assert c.get('/api/projects').status_code == 401
    assert c.get('/api/session', headers={'Origin':'https://untrusted.example'}).status_code == 403
    assert c.get('/api/session', headers={'Host':'attacker.example'}).status_code == 403
    assert c.get('/api/session', headers={'Sec-Fetch-Site':'cross-site'}).status_code == 403
    assert c.get('/api/session').status_code == 200
    assert c.post('/api/demo').status_code == 403
    assert c.post('/api/control/commands', headers=HEADERS).status_code == 404
    assert c.get('/api/health').json()['equipment_control'] is False


def test_duplicate_import_is_idempotent_and_rejected_import_is_atomic(setup):
    c,p,store,_ = setup
    path = f"/api/projects/{p['id']}"
    count = len(c.get(path+'/datasets').json())
    before = store.audit_history()['head']
    response = c.post(path+'/imports',data={'kind':'telemetry'},files={'file':('sample.csv',demo.telemetry(),'text/csv')})
    assert response.status_code == 201
    assert response.json()['duplicate'] is True
    assert len(c.get(path+'/datasets').json()) == count
    bad = c.post(path+'/imports',data={'kind':'telemetry'},files={'file':('bad.csv',b'bad,header\n1,2','text/csv')})
    assert bad.status_code == 422
    assert len(c.get(path+'/datasets').json()) == count
    assert store.audit_history()['head'] == before


def test_project_separation(setup):
    c,p,_,_ = setup
    other=c.post('/api/projects',json={'name':'Other','well_name':'Other','datum':'RKB','bit_diameter_m':.2,'origin':'historical'}).json()
    dataset=c.get(f"/api/projects/{p['id']}/datasets").json()[0]
    assert c.get(f"/api/projects/{other['id']}/datasets/{dataset['id']}").status_code == 404
    assert c.get('/api/projects/not-found/events').status_code == 404


def test_report_is_fixed_verified_and_persists_after_restart(setup):
    c,p,store,root=setup
    path=f"/api/projects/{p['id']}"
    body={'tvd_m':1000,'density_kg_m3':1000,'surface_gauge_pa':0,'annular_loss_pa':0,'pore_gauge_pa':8e6,'fracture_gauge_pa':12e6}
    calc=c.post(path+'/calculations/pressure',json=body)
    assert calc.status_code==200
    report=c.post(path+'/reports')
    assert report.status_code==201, report.text
    report_path=path+'/reports/'+report.json()['id']
    assert c.get(path+'/reports').json()[0]['id']==report.json()['id']
    before=c.get(report_path).json()
    exported=c.get(report_path+'/download')
    assert exported.status_code==200
    assert exported.headers['content-disposition'].startswith('attachment;')
    assert exported.json()==before
    assert before['sha256']==hashlib.sha256(canonical(before['snapshot']).encode()).hexdigest()
    assert len(before['snapshot']['calculations'])==1
    event=c.get(path+'/events').json()[0]
    ack=c.post(path+f"/events/{event['id']}/acknowledge",json={'note':'Reviewed synthetic missing sensor value.'})
    assert ack.status_code==200
    assert c.get(report_path).json()==before
    after=TestClient(create_app(root))
    after.get('/api/session')
    assert after.get(report_path).json()==before
    assert after.get(path+'/events').json()[0]['acknowledgement']['note']=='Reviewed synthetic missing sensor value.'
    assert store.audit_history()['integrity']=='verified'


def test_file_tampering_blocks_read_and_report(setup):
    c,p,store,root=setup
    path=f"/api/projects/{p['id']}"
    dataset=c.get(path+'/datasets').json()[0]
    file=root/'parquet'/f"{dataset['id']}.parquet"
    file.write_bytes(b'corrupted')
    assert c.get(path+'/datasets/'+dataset['id']).status_code==422
    assert c.post(path+'/reports').status_code==422


def test_raw_source_tampering_blocks_report(setup):
    c,p,_,root=setup
    dataset=c.get(f"/api/projects/{p['id']}/datasets").json()[0]
    (root/'raw'/dataset['source_hash']).write_bytes(b'changed')
    assert c.post(f"/api/projects/{p['id']}/reports").status_code==422


def test_append_only_audit_and_ack_idempotence(setup):
    c,p,store,_=setup
    path=f"/api/projects/{p['id']}"
    event=c.get(path+'/events').json()[0]
    endpoint=path+f"/events/{event['id']}/acknowledge"
    a=c.post(endpoint,json={'note':'First review'}).json()
    b=c.post(endpoint,json={'note':'Changed review'}).json()
    assert a==b
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('DELETE FROM audit')


def test_nonfinite_and_extra_fields_rejected(setup):
    c,p,_,_=setup
    path=f"/api/projects/{p['id']}/calculations/mse"
    base={'wob_n':100000,'torque_nm':5000,'rotation_rad_s':5,'rop_m_s':.01,'bit_diameter_m':.2}
    assert c.post(path,json={**base,'command':'write'}).status_code==422
    assert c.post(path,content=json.dumps({**base,'wob_n':'NaN'})).status_code==422


def test_large_upload_rejected(setup):
    c,p,_,_=setup
    response=c.post(f"/api/projects/{p['id']}/imports",data={'kind':'telemetry'},files={'file':('large.csv',b'0'*(2*1024*1024+1),'text/csv')})
    assert response.status_code==413


def test_demo_load_does_not_duplicate(setup):
    c,p,_,_=setup
    assert c.post('/api/demo').json()['id']==p['id']
    assert len(c.get('/api/projects').json())==1
