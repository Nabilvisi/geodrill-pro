import base64
import copy
import hashlib
import io
import json
from uuid import uuid4
import pytest
from fastavro import schemaless_writer
from packages.streaming import capture, fixtures, wire
from services.api.storage import Store


def record(name, body, mid=2, flags=2, correlation=0, sequence=1, session="s", mode="synthetic_fixture"):
    raw=wire.encode(name,body,mid,correlation,flags,fixture=True)
    return {"wire_base64":base64.b64encode(raw).decode(),"wire_sha256":hashlib.sha256(raw).hexdigest(),
            "session_id":session,"sequence":sequence,"received_at_utc":"2026-10-06T12:00:00+00:00",
            "transport_event":None,"mode":mode}


def state():
    s=capture.ChannelState(capture.SourceConfig.model_validate(fixtures.configuration()))
    r=record("GetChannelMetadataResponse",{"metadata":{"a":fixtures.metadata()}})
    assert s.consume(r)["status"]=="retained"
    return s


def data(s, rows, mid=4, **kw):
    return s.consume(record("ChannelData",{"data":rows},mid,**kw))


def test_independent_avro_ping_bytes_and_customer_write_allowlist():
    raw=wire.encode("Ping",{"currentDateTime":1000},2,fixture=True)
    assert raw==b"\x00\x10\x00\x04\x04\xd0\x0f"
    assert wire.decode(raw)["body"]=={"currentDateTime":1000}
    with pytest.raises(ValueError,match="read-only"):
        wire.encode("ChannelData",{"data":[]},1)
    with pytest.raises(ValueError,match="sequence"):
        wire.encode("Ping",{"currentDateTime":0},2)


@pytest.mark.parametrize("raw",[b"",b"\xff",b"\x00\x10\x00\x04\x04",b"\x00\x10\x00\x04\x04\x00junk"])
def test_malformed_and_trailing_bytes_rejected(raw):
    with pytest.raises(ValueError):wire.decode(raw)


def test_duplicate_late_conflict_and_explicit_range_repair_preserve_scope():
    s=state();a=data(s,[fixtures.point()]);assert a["point_statuses"][0]["status"]=="accepted"
    assert s.points[fixtures.CHANNEL_URI,fixtures.TIME_US]["value_si"]==12e6
    assert data(s,[fixtures.point()],6)["point_statuses"][0]["status"]=="duplicate"
    assert data(s,[fixtures.point(fixtures.TIME_US-1)],8)["point_statuses"][0]["status"]=="out_of_order_quarantined"
    assert data(s,[fixtures.point(value=13.)],10)["point_statuses"][0]["status"]=="conflicting_index"
    assert s.points[fixtures.CHANNEL_URI,fixtures.TIME_US]["quality"]=="withheld_conflict"
    replace=record("RangeReplaced",{"changeTime":fixtures.TIME_US+2,"channelIds":[42],"changedInterval":fixtures.interval(),"data":[fixtures.point(value=14.)]},12)
    s.consume(replace);assert s.points[fixtures.CHANNEL_URI,fixtures.TIME_US]["value_si"]==14e6
    assert len(s.receipts)==6 and not s.view()["equipment_control"]


def test_multipart_replacement_does_not_delete_until_fin_and_handles_elided_index():
    s=state();data(s,[fixtures.point()])
    body={"changeTime":fixtures.TIME_US+2,"channelIds":[42],"changedInterval":fixtures.interval(),"data":[fixtures.point(value=14.)]}
    s.consume(record("RangeReplaced",body,6,flags=0))
    assert s.points[fixtures.CHANNEL_URI,fixtures.TIME_US]["value_si"]==12e6
    final=copy.deepcopy(body);final["data"]=[fixtures.point(fixtures.TIME_US+1,15.)]
    s.consume(record("RangeReplaced",final,8,correlation=6))
    assert len(s.points)==2 and s.points[fixtures.CHANNEL_URI,fixtures.TIME_US]["value_si"]==14e6


def test_duplicate_sequence_quarantines_and_invalid_value_is_atomic():
    s=state();data(s,[fixtures.point()]);r=data(s,[fixtures.point(fixtures.TIME_US+1)],4)
    assert r["status"]=="quarantined" and len(s.points)==1
    r=data(s,[fixtures.point(fixtures.TIME_US+1),fixtures.point(fixtures.TIME_US+2,float("nan"))],6)
    assert r["status"]=="quarantined" and len(s.points)==1


def test_null_negative_attributes_and_clock_ahead_are_retained_without_eligibility():
    s=state();p=fixtures.point(fixtures.TIME_US+200000000,-1.)
    p["valueAttributes"]=[];data(s,[p]);point=next(iter(s.points.values()))
    assert point["original_value"]==-1. and point["quality"]=="negative_observation"
    data(s,[fixtures.point(fixtures.TIME_US+201000000,None)],6)
    assert s.points[fixtures.CHANNEL_URI,fixtures.TIME_US+201000000]["value_si"] is None


@pytest.mark.parametrize("patch",[{"uom":"psi"},{"dataKind":"typeString"},{"axisVectorLengths":[2]},{"channelClassUri":"missing"},{"uri":"eml:///witsml20.Channel(01234567-89ab-4cde-8012-3456789abcde)"}])
def test_incompatible_metadata_is_quarantined(patch):
    s=state();r=s.consume(record("GetChannelMetadataResponse",{"metadata":{"bad":fixtures.metadata(channel_id=43,**patch)}},4))
    assert r["status"]=="quarantined" and 43 not in s.metadata


def test_receipts_duplicate_wire_restart_report_and_project_restore(tmp_path):
    store=Store(tmp_path/"original")
    p=store.create_project({"name":"Synthetic capture","well_name":"Generated","datum":"RKB","bit_diameter_m":.2,"origin":"synthetic"})
    src=capture.create_source(store,p["id"],fixtures.configuration());session=str(uuid4())
    messages=fixtures.generated_messages()
    for raw in messages:
        capture.preserve(store,p["id"],src["id"],raw,session,mode="synthetic_fixture")
    # The exact same wire bytes get a second receipt, not deduplicated metadata.
    capture.preserve(store,p["id"],src["id"],messages[-1],session,mode="synthetic_fixture")
    records=capture.envelopes(store,p["id"],src["id"])
    assert len(records)==8 and len({r["id"] for r in records})==8
    assert base64.b64decode(records[0]["wire_base64"])==messages[0]
    before=capture.materialize(store,p["id"],src["id"]).view(at="2026-10-06T12:00:00Z")
    assert before["stale"] and before["points"][0]["value_si"]==11.5e6
    restart=Store(store.root);assert capture.materialize(restart,p["id"],src["id"]).view(at="2026-10-06T12:00:00Z")==before
    report=store.create_report(p["id"]);snapshot=store.report(p["id"],report["id"])["snapshot"]
    assert len([d for d in snapshot["datasets"] if d["kind"]=="etp_capture"])==8
    restored=Store(tmp_path/"restored");restored.restore_bundle(store.export_bundle(p["id"]))
    assert capture.materialize(restored,p["id"],src["id"]).view(at="2026-10-06T12:00:00Z")==before
    assert restored.audit_history()["integrity"]=="verified"


def test_foreign_source_and_corrupted_original_wire_are_rejected(tmp_path):
    store=Store(tmp_path);p=store.create_project({"origin":"synthetic"});other=store.create_project({"origin":"synthetic"})
    src=capture.create_source(store,p["id"],fixtures.configuration())
    with pytest.raises(KeyError):capture.source(store,other["id"],src["id"])
    d=capture.preserve(store,p["id"],src["id"],fixtures.generated_messages()[0],str(uuid4()),mode="synthetic_fixture")
    record=store.dataset(p["id"],d["id"]);(store.root/"raw"/record["source_hash"]).write_bytes(b"tampered")
    with pytest.raises(ValueError,match="hash"):capture.envelopes(store,p["id"],src["id"])


@pytest.mark.parametrize("endpoint",["ws://external.example/etp","wss://user:secret@example/etp","wss://example/etp?token=x","https://example/etp"])
def test_insecure_or_credential_bearing_endpoint_rejected(endpoint):
    value=fixtures.configuration();value["endpoint"]=endpoint
    with pytest.raises(ValueError):capture.SourceConfig.model_validate(value)
