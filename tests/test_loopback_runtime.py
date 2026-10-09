"""Chosen loopback ports retain host/origin/session gates and process ownership."""
import hashlib
import os
import sys
import socket
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient
from packages.loopback import checked_port, local_health, require_owned_service, runtime_identity
from packages.version import APP_VERSION
from services.api.main import create_app
from tools import desktop_app, launch


def owned(installation, runtime):
    return {"status":"ok", "version":APP_VERSION, "equipment_control":False,
            "instance_id":hashlib.sha256(str(installation.resolve()).encode()).hexdigest()[:16],
            "runtime_id":runtime_identity(runtime), "pid":os.getpid()}


@pytest.mark.parametrize("value", [0, -1, 65536, True, 1.5, "host:8890", "8890.0"])
def test_bad_port_cannot_create_or_migrate_data(tmp_path, value):
    destination=tmp_path/'must-remain-absent'
    with pytest.raises(ValueError):
        create_app(destination, loopback_port=value)
    assert not destination.exists()


def test_chosen_port_retains_host_origin_session_and_mutation_guards(tmp_path):
    with TestClient(create_app(tmp_path,loopback_port=8890),base_url='http://127.0.0.1:8890') as client:
        health=client.get('/api/health').json()
        assert health['runtime_id']==runtime_identity(tmp_path)
        assert client.get('/api/projects').status_code==401
        client.get('/api/session')
        assert client.get('/api/projects').status_code==200
        assert client.get('/api/projects',headers={'Host':'127.0.0.1:8891'}).status_code==403
        assert client.get('/api/projects',headers={'Host':'outside.example:8890'}).status_code==403
        assert client.get('/api/projects',headers={'Origin':'http://127.0.0.1:8891'}).status_code==403
        assert client.get('/api/projects',headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
        assert client.post('/api/projects',json={'name':'test'}).status_code==403


def test_two_ports_keep_independent_browser_sessions(tmp_path):
    with TestClient(create_app(tmp_path/'a',loopback_port=8890),base_url='http://127.0.0.1:8890') as a, \
         TestClient(create_app(tmp_path/'b',loopback_port=8891),base_url='http://127.0.0.1:8891') as b:
        a.get('/api/session');b.get('/api/session')
        # Browser cookies share the hostname across ports. Both must coexist.
        a.cookies.update(b.cookies);b.cookies.update(a.cookies)
        assert a.get('/api/projects').status_code==b.get('/api/projects').status_code==200
        assert a.cookies.get('gd_session_8890')!=a.cookies.get('gd_session_8891')


@pytest.mark.parametrize('response', [httpx.Response(404), httpx.Response(200,text='<html>other app</html>'),
                                   httpx.Response(200,json=[]), httpx.Response(200,json={})])
def test_unknown_live_service_is_not_treated_as_a_free_port(monkeypatch,response):
    monkeypatch.setattr('packages.loopback.loopback_port_available',lambda port:False)
    monkeypatch.setattr('packages.loopback.httpx.get',lambda *a,**kw:response)
    assert local_health(8890)=={'unidentified_service':True}


def test_probe_is_fixed_loopback_and_does_not_follow_proxy_or_redirects(monkeypatch):
    observed={}
    def probe(url,**kwargs):
        observed.update(url=url,**kwargs)
        raise httpx.ConnectError('unused local port')
    monkeypatch.setattr('packages.loopback.httpx.get',probe)
    monkeypatch.setattr('packages.loopback.loopback_port_available',lambda port:False)
    assert local_health(8890)=={'unidentified_service':True}
    assert observed=={'url':'http://127.0.0.1:8890/api/health','timeout':1,'follow_redirects':False,'trust_env':False}


def test_actual_listener_blocks_reuse_while_free_port_needs_no_http_probe(monkeypatch):
    monkeypatch.setattr('packages.loopback.httpx.get',lambda *a,**kw:httpx.Response(404))
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as listener:
        listener.bind(('127.0.0.1',0));listener.listen(1)
        port=listener.getsockname()[1]
        assert local_health(port)=={'unidentified_service':True}
    monkeypatch.setattr('packages.loopback.httpx.get',lambda *a,**kw:pytest.fail('A bind-confirmed free port needs no HTTP probe'))
    assert local_health(port) is None


@pytest.mark.parametrize('change', [{'instance_id':'foreign'}, {'runtime_id':'another data directory'},
                                  {'version':'older build'}, {'pid':0}, {'pid':-1}, {'pid':True}])
def test_reuse_or_stop_rejects_foreign_installation_data_version_and_pid(tmp_path,change):
    state={**owned(tmp_path,tmp_path/'data'),**change}
    with pytest.raises(RuntimeError,match='existing service was left running'):
        require_owned_service(state,tmp_path,tmp_path/'data',8890)


def test_desktop_collision_does_not_start_the_api_or_open_another_app(tmp_path,monkeypatch):
    runtime=tmp_path/'isolated-data'
    monkeypatch.setenv('GEODRILL_DATA_DIR',str(runtime))
    monkeypatch.setattr(sys,'argv',['GeoDrillPro.exe','--port','8890'])
    monkeypatch.setattr(desktop_app,'local_health',lambda port:{'unidentified_service':True})
    monkeypatch.setattr(desktop_app,'create_app',lambda **kw:pytest.fail('Must refuse before creating the API'))
    monkeypatch.setattr(desktop_app.webbrowser,'open',lambda url:pytest.fail('Must not open the other app'))
    assert desktop_app.main()==1
    assert not (runtime/'workspace.sqlite').exists()


def test_desktop_reuses_only_its_exact_installation_and_data(tmp_path,monkeypatch):
    monkeypatch.setenv('GEODRILL_DATA_DIR',str(tmp_path))
    monkeypatch.setattr(sys,'argv',['GeoDrillPro.exe','--port','8890','--no-browser'])
    monkeypatch.setattr(desktop_app,'local_health',lambda port:owned(desktop_app.BUNDLE_DIR,tmp_path))
    monkeypatch.setattr(desktop_app,'create_app',lambda **kw:pytest.fail('A reused service must not create another API'))
    assert desktop_app.main()==0


def test_desktop_forwards_port_to_app_and_keeps_listener_on_loopback(tmp_path,monkeypatch):
    captured={}
    monkeypatch.setenv('GEODRILL_DATA_DIR',str(tmp_path))
    monkeypatch.setattr(sys,'argv',['GeoDrillPro.exe','--port','8890','--no-browser'])
    monkeypatch.setattr(desktop_app,'local_health',lambda port:None)
    def app(**kwargs):
        captured.update(kwargs);return 'synthetic test app'
    monkeypatch.setattr(desktop_app,'create_app',app)
    def config(app,**kwargs):
        captured.update(kwargs);return app
    monkeypatch.setattr(desktop_app.uvicorn,'Config',config)
    class Server:
        started=True
        def __init__(self,config):pass
        def run(self):pass
    monkeypatch.setattr(desktop_app.uvicorn,'Server',Server)
    assert desktop_app.main()==0
    assert captured['data_dir']==tmp_path and captured['loopback_port']==8890
    assert captured['host']=='127.0.0.1' and captured['port']==8890


def test_source_stop_leaves_an_unidentified_service_running(tmp_path,monkeypatch):
    monkeypatch.setenv('GEODRILL_DATA_DIR',str(tmp_path))
    monkeypatch.setattr(sys,'argv',['launch.py','--stop','--port','8890'])
    monkeypatch.setattr(launch,'health',lambda port:{'unidentified_service':True})
    monkeypatch.setattr(launch.os,'kill',lambda *args:pytest.fail('Must not stop another application'))
    with pytest.raises(SystemExit,match='existing service was left running'):
        launch.main()


def test_source_launch_passes_chosen_port_and_waits_for_owned_data(tmp_path,monkeypatch):
    installation=tmp_path/'installation';installation.mkdir()
    (installation/'index.html').write_text('synthetic test asset')
    runtime=tmp_path/'data'
    monkeypatch.setattr(launch,'ROOT',installation)
    monkeypatch.setenv('GEODRILL_DATA_DIR',str(runtime))
    monkeypatch.setattr(sys,'argv',['launch.py','--no-browser','--port','8890'])
    monkeypatch.setattr(launch,'frontend_dist',lambda root:installation)
    states=iter([None,owned(installation,runtime)]);ports=[]
    def health(port):
        ports.append(port);return next(states)
    monkeypatch.setattr(launch,'health',health)
    commands=[]
    monkeypatch.setattr(launch.subprocess,'Popen',lambda args,**kwargs:commands.append(args))
    launch.main()
    assert ports==[8890,8890]
    assert commands[0][-2:]==['--port','8890']
