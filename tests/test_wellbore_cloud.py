"""The hosted transport must preserve the same source/ownership gates."""
import base64
import json
import pytest
from apps.streamlit.cloud import Workspace


def test_cloud_owned_revision_workflow_and_scope_headers():
    workspace=Workspace(seed=False)
    try:
        p=workspace.call('POST','/api/v1/projects',json={'name':'Synthetic cloud scope','origin':'synthetic','datum':'MSL'})
        well=workspace.call('POST',f"/api/v1/projects/{p['id']}/wells",json={'name':'Cloud well'})
        wb=workspace.call('POST',f"/api/v1/wells/{well['id']}/wellbores",json={'name':'Cloud bore'})
        other=workspace.call('POST',f"/api/v1/wells/{well['id']}/wellbores",json={'name':'Other bore'})
        source=workspace.call('POST',f"/api/v1/wellbores/{wb['id']}/surveys",json={'trajectory_type':'planned','change_note':'Synthetic authored test','frame':{'datum':'MSL','north_reference':'true','coordinate_reference':'Synthetic shared local frame','wellhead_north_m':0,'wellhead_east_m':0,'wellhead_elevation_m':0},'evidence_state':'synthetic','survey_quality_note':'Synthetic software case','survey':{'stations':[{'md_m':0,'inclination_rad':0,'azimuth_rad':0},{'md_m':100,'inclination_rad':.1,'azimuth_rad':.2}]}})
        t=workspace.call('POST',f"/api/v1/wellbores/{wb['id']}/trajectories",json={'survey_revision_id':source['id'],'change_note':'Saved cloud trajectory'})
        request={'id':'scope-test','method':'GET','path':f"/api/projects/{p['id']}/geometry/{t['id']}",'headers':{'x-geodrill-wellbore':other['id'],'x-geodrill-trajectory-type':'planned'}}
        response=workspace.execute(request)
        assert response['status']==422 and 'selected wellbore' in base64.b64decode(response['body_base64']).decode()
        request.update(id='correct-scope',headers={'x-geodrill-wellbore':wb['id'],'x-geodrill-trajectory-type':'planned'})
        assert workspace.execute(request)['status']==200
        request.update(id='bad-header',headers={'Authorization':'Bearer untrusted'})
        with pytest.raises(ValueError,match='scope headers'):workspace.execute(request)
        report=workspace.call('POST',f"/api/projects/{p['id']}/reports")
        download=workspace.execute({'id':'fixed-report','method':'GET','path':f"/api/projects/{p['id']}/reports/{report['id']}/download"})
        raw=base64.b64decode(download['body_base64']);snapshot=json.loads(raw)
        assert snapshot['snapshot']['wellbore_state']['revisions'][0]['wellbore_id']==wb['id']
        assert list(workspace.report_downloads.values())==[raw]
    finally:workspace.close()
