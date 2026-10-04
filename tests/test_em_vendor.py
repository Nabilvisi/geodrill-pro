import copy
import json
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from packages.engineering.em_vendor import EMVendorDocument, EMReviewInput, review_vendor
from services.api import demo
from services.api.main import create_app
from test_geometry_casing import api_setup

def document():
    return EMVendorDocument.model_validate_json(demo.em_vendor("Test","RKB"))

def inputs(**patch):
    return EMReviewInput.model_validate({**{
        "study_name":"Vendor fixture","dataset_id":"fixture","geometry_revision_id":"fixture","depth_datum":"RKB",
        "alignment_status":"supplied_confirmed","md_offset_m":0.,
        "depth_alignment_note":"Native MD tied to the test survey","reviewer_note":"Software evidence only"},**patch})

def test_native_values_quality_uncertainty_and_receipt_delay_preserved():
    d=document();r=review_vendor(d,inputs(),1000.)
    assert r["eligible_count"]==5 and r["withheld_count"]==3
    assert [x["source_index"] for x in r["rows"]]==list(range(8))
    assert r["rows"][0]["display"]["rh_ohm_m"]==10.
    assert r["rows"][0]["display"]["rh_interval"]=={"lower":8.,"upper":12.,"meaning":"Synthetic parameter range; not calibrated confidence"}
    assert r["rows"][0]["receipt_delay_s"]==12.
    assert r["rows"][4]["receipt_delay_s"] is None
    assert all(r["rows"][i]["display"] is None for i in (3,6,7))
    assert r["rows"][6]["supplied"]["rh_ohm_m"]==22.
    assert r["missing_resistivity_interval_count"]==5  # all displayed Rv have no interval
    assert not r["native_inversion_available"] and not r["interpretation_approved"] and r["steering_authority"]=="none"
    assert not any(r["integration_readiness"].values())

def test_offset_is_added_only_to_native_md_not_boundary_or_tool_spacing():
    payload=document().model_dump();payload["tool"]["tool_to_bit_offset_m"]=25.
    d=EMVendorDocument.model_validate(payload);r=review_vendor(d,inputs(md_offset_m=7.5),1000.)
    assert r["rows"][0]["native_md_m"]==100.
    assert r["rows"][0]["aligned_md_m"]==107.5
    assert r["rows"][0]["display"]["boundary_distance_m"]==5.
    assert r["tool"]["tool_to_bit_offset_m"]==25.
    assert r["integration_readiness"]["declared_tool_to_bit_offset"]

def test_unverified_alignment_withholds_every_sample_without_losing_source():
    r=review_vendor(document(),inputs(alignment_status="unverified"),1000.)
    assert r["status"]=="withheld" and r["withheld_count"]==8
    assert all(x["display"] is None and x["supplied"] for x in r["rows"])

def test_survey_envelope_and_datum_gate():
    r=review_vendor(document(),inputs(md_offset_m=-105.),100.)
    assert r["rows"][0]["display"] is None
    assert r["rows"][1]["aligned_md_m"]==5.
    assert r["rows"][1]["display"] is not None
    with pytest.raises(ValueError,match="datum"):
        review_vendor(document(),inputs(depth_datum="MSL"),1000.)

@pytest.mark.parametrize("changes",[
    {"acquired_at":"2026-01-01T00:00:00"},
    {"acquired_at":"not-a-time"},
    {"received_at":"2025-12-31T23:59:59Z"},
    {"rh_ohm_m":0.},
    {"rv_ohm_m":-1.},
    {"rh_ohm_m":float("nan")},
    {"rh_interval":{"lower":11.,"upper":12.,"meaning":"Wrong bounds"}},
    {"rh_interval":{"lower":-1.,"upper":12.,"meaning":"Invalid lower"}},
    {"rh_interval":{"lower":8.,"upper":1e8,"meaning":"Outside envelope"}},
    {"rh_interval":{"lower":12.,"upper":8.,"meaning":"Reversed bounds"}},
    {"boundary_reference":None},
    {"boundary_interval":{"lower":6.,"upper":7.,"meaning":"Wrong bounds"}},
    {"boundary_interval":{"lower":-20000.,"upper":7.,"meaning":"Outside envelope"}},
    {"misfit":1.,"misfit_definition":None},
    {"quality":"approved"},
])
def test_invalid_sample_contracts_are_rejected(changes):
    value=document().model_dump();value["samples"][0].update(changes)
    with pytest.raises(ValidationError):EMVendorDocument.model_validate(value)

def test_utc_offset_arithmetic_does_not_assume_local_timezone():
    data=document().model_dump();data["samples"][0]["acquired_at"]="2026-01-01T07:00:00+07:00"
    data["samples"][0]["received_at"]="2026-01-01T00:00:12Z"
    r=review_vendor(EMVendorDocument.model_validate(data),inputs(),1000.)
    assert r["rows"][0]["receipt_delay_s"]==12.

@pytest.mark.parametrize("field,changes",[
    ("resistivity_unit","OHMM"),("boundary_distance_unit","ft"),
    ("schema_version","vendor-v2"),("origin","measured"),
    ("samples",[]),
])
def test_unsupported_units_versions_and_empty_sources_rejected(field,changes):
    data=document().model_dump();data[field]=changes
    with pytest.raises(ValidationError):EMVendorDocument.model_validate(data)

def test_instrument_facts_and_source_order_validation():
    data=document().model_dump();data["samples"][1]["md_m"]=100.
    with pytest.raises(ValidationError):EMVendorDocument.model_validate(data)
    data=document().model_dump();data["tool"]["frequencies_hz"]=[0.]
    with pytest.raises(ValidationError):EMVendorDocument.model_validate(data)
    data=document().model_dump();data["tool"]["transmitter_receiver_spacings_m"]=[float("inf")]
    with pytest.raises(ValidationError):EMVendorDocument.model_validate(data)

def test_qualification_reference_is_only_supplied_evidence():
    data=document().model_dump();data["tool"]["qualification_reference"]="Supplied test document; not checked"
    r=review_vendor(EMVendorDocument.model_validate(data),inputs(),1000.)
    assert r["integration_readiness"]["supplied_qualification_reference"]
    assert not r["interpretation_approved"] and not r["native_inversion_available"]

def test_api_round_trip_duplicate_report_restart_and_source_integrity(api_setup):
    c,p,base,d,store,root=api_setup
    revision=c.post(base+"/geometry",json={"geometry":d,"change_note":"EM source context"}).json()
    raw=demo.em_vendor("Test","RKB")
    imported=c.post(base+"/em-vendor/imports",files={"file":("vendor.json",raw,"application/json")})
    assert imported.status_code==201,imported.text
    imported=imported.json()
    duplicate=c.post(base+"/em-vendor/imports",files={"file":("same.json",raw,"application/json")}).json()
    assert duplicate["duplicate"] and duplicate["id"]==imported["id"]
    source=c.get(base+"/datasets/"+imported["id"]).json()
    assert source["row_count"]==8 and source["kind"]=="em_vendor"
    assert json.loads(source["rows"][0]["supplied_json"])["rh_ohm_m"]==10.
    value=inputs(dataset_id=source["id"],geometry_revision_id=revision["id"]).model_dump()
    response=c.post(base+"/calculations/em-vendor",json=value)
    assert response.status_code==200,response.text
    saved=response.json()
    assert saved["result"]["source_sha256"]==source["source_hash"]
    assert saved["result"]["parquet_sha256"]==source["parquet_sha256"]
    assert saved["result"]["geometry_sha256"]==revision["sha256"]
    report=c.post(base+"/reports").json();snapshot=c.get(base+"/reports/"+report["id"]).json()
    assert saved in snapshot["snapshot"]["calculations"]
    after=TestClient(create_app(root));after.get("/api/session")
    assert after.get(base+"/calculations?model=em_vendor").json()==[saved]
    assert c.post(base+"/calculations/em-vendor",json={**value,"depth_datum":"MSL"}).status_code==422
    with store.connect() as db:
        with pytest.raises(Exception,match="immutable"):db.execute("DELETE FROM calculations WHERE id=?",(saved["id"],))
    (root/"raw"/source["source_hash"]).write_bytes(b"damaged")
    assert c.post(base+"/calculations/em-vendor",json=value).status_code==422
    assert c.get(base+"/reports/"+report["id"]).json()==snapshot

def test_api_document_project_matching_wrong_sources_and_template(api_setup):
    c,p,base,d,store,root=api_setup
    revision=c.post(base+"/geometry",json={"geometry":d,"change_note":"EM context"}).json()
    for well,datum in (("Other","RKB"),("Test","MSL")):
        assert c.post(base+"/em-vendor/imports",files={"file":("source.json",demo.em_vendor(well,datum),"application/json")}).status_code==422
    assert c.post(base+"/em-vendor/imports",files={"file":("source.txt",demo.em_vendor("Test","RKB"),"text/plain")}).status_code==422
    assert c.post(base+"/em-vendor/imports",files={"file":("source.json",b"{oops","application/json")}).status_code==422
    assert c.post(base+"/calculations/em-vendor",json=inputs(dataset_id=d["survey_dataset_id"],geometry_revision_id=revision["id"]).model_dump()).status_code==422
    example=c.post(base+"/examples/em-vendor")
    assert example.status_code==201
    assert c.post(base+"/examples/em-vendor").json()["duplicate"]
    historical=c.post("/api/projects",json={"name":"History","well_name":"Test","datum":"RKB","origin":"historical","bit_diameter_m":.2}).json()
    other="/api/projects/"+historical["id"]
    assert c.post(other+"/examples/em-vendor").status_code==422
    assert c.post(other+"/em-vendor/imports",files={"file":("synthetic.json",demo.em_vendor("Test","RKB"),"application/json")}).status_code==422
    assert c.post(other+"/calculations/em-vendor",json=inputs(dataset_id=example.json()["id"],geometry_revision_id=revision["id"]).model_dump()).status_code==404
    template=c.get(other+"/em-vendor/template")
    assert template.status_code==200 and template.json()["origin"]=="synthetic"
    data=json.loads(demo.em_vendor("Test","RKB"));data["origin"]="historical"
    assert c.post(other+"/em-vendor/imports",files={"file":("record.json",json.dumps(data),"application/json")}).status_code==201

def test_parquet_corruption_blocks_new_review(api_setup):
    c,p,base,d,store,root=api_setup
    revision=c.post(base+"/geometry",json={"geometry":d,"change_note":"EM context"}).json()
    source=c.post(base+"/examples/em-vendor").json()
    (root/"parquet"/(source["id"]+".parquet")).write_bytes(b"invalid")
    value=inputs(dataset_id=source["id"],geometry_revision_id=revision["id"]).model_dump()
    assert c.post(base+"/calculations/em-vendor",json=value).status_code==422
