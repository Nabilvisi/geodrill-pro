"""Durable original-wire capture, project binding and a declared scalar channel profile.

Captures use existing immutable raw/Parquet datasets, audit, report and archive paths.
Every receipt has its own envelope, including duplicate wire bytes and quarantine.
"""
import base64
import hashlib
import json
import math
import re
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
from urllib.parse import urlsplit
from pydantic import Field, model_validator
from packages.engineering.models import Contract
from packages.engineering.ingestion import CHANNELS, CANONICAL
from services.api.storage import canonical, now
from .wire import decode, MAX_MESSAGE

PROFILE = "GD-A07-etp12-witsml21-scalar-1"
MAX_CAPTURES = 10000
MAX_POINTS = 100000
URI = re.compile(r"eml:///(?:dataspace\('[^'\x00-\x1f]{1,160}'\)/)?witsml21\.Channel\(([0-9a-fA-F-]{36})\)$")


def channel_uri(value):
    match = URI.fullmatch(value)
    if not match:
        raise ValueError("Expected an explicit WITSML 2.1 Channel URI")
    UUID(match[1])
    return value


def micros(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 7258118400000000:
        raise ValueError("DateTime index must be UTC Unix microseconds in the supported 1970–2200 range")
    return value


def iso(value):
    return (datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=micros(value))).isoformat()


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Receipt time requires an explicit timezone")
    return parsed.astimezone(timezone.utc)


def json_value(value):
    if isinstance(value, bytes):
        return {"bytes_base64": base64.b64encode(value).decode("ascii")}
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": repr(value)}
    return value


class ChannelBinding(Contract):
    uri: str = Field(min_length=1, max_length=512)
    quantity: str = Field(min_length=1, max_length=20)
    unit: str = Field(min_length=1, max_length=30)
    property_kind_uri: str = Field(min_length=1, max_length=512)
    mapping_basis: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def supported(self):
        channel_uri(self.uri)
        if self.quantity not in CHANNELS or self.unit not in CHANNELS[self.quantity]:
            raise ValueError("Quantity/unit is outside the declared scalar telemetry profile")
        return self


class SourceConfig(Contract):
    name: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=1, max_length=512)
    authorization_basis: str = Field(min_length=1, max_length=1000)
    channels: list[ChannelBinding] = Field(min_length=1, max_length=32)
    stale_after_s: float = Field(ge=1, le=86400, default=30.)
    origin: str = Field(pattern="^(historical|synthetic)$", default="historical")
    loopback_fixture: bool = False

    @model_validator(mode="after")
    def endpoint_profile(self):
        url = urlsplit(self.endpoint)
        if not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("ETP endpoint must have a host and contain no credentials, query or fragment")
        if url.scheme != "wss":
            if not (self.loopback_fixture and self.origin == "synthetic" and url.scheme == "ws"
                    and url.hostname in {"127.0.0.1", "localhost", "::1"}):
                raise ValueError("ETP requires wss; ws is limited to explicit synthetic loopback fixtures")
        if len({c.uri for c in self.channels}) != len(self.channels):
            raise ValueError("Channel bindings must have unique URIs")
        return self


def create_source(store, project_id, config):
    project = store.project(project_id)
    config = SourceConfig.model_validate(config)
    if config.loopback_fixture and project["origin"] != "synthetic":
        raise ValueError("Fixture transport requires a synthetic project")
    raw = canonical(config.model_dump()).encode("utf-8")
    record = store.import_data(project_id, "etp_source", "etp-source.json", raw,
                              [{"configuration_json": raw.decode()}], {"profile": PROFILE}, [])
    return {"id": record["id"], "duplicate": record["duplicate"], "configuration": config.model_dump(),
            "profile": PROFILE, "equipment_authority": "none", "outbound_connection_started": False}


def source(store, project_id, source_id):
    record = store.dataset(project_id, source_id)
    if record["kind"] != "etp_source" or record["metadata"].get("profile") != PROFILE:
        raise ValueError("Expected a streaming source in this project")
    raw = (store.root / "raw" / record["source_hash"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != record["source_hash"]:
        raise ValueError("Streaming source hash mismatch")
    config = SourceConfig.model_validate_json(raw)
    if canonical(config.model_dump()) != record["rows"][0]["configuration_json"]:
        raise ValueError("Streaming source differs from preserved normalized evidence")
    return config


def envelopes(store, project_id, source_id):
    source(store, project_id, source_id)
    records = [d for d in store.datasets(project_id) if d["kind"] == "etp_capture"
               and d["metadata"].get("source_id") == source_id]
    if len(records) > MAX_CAPTURES:
        raise ValueError("Streaming capture count exceeds this profile's bounded replay")
    records.sort(key=lambda d: d["metadata"]["sequence"])
    values = []
    for index, d in enumerate(records, 1):
        if d["metadata"]["sequence"] != index:
            raise ValueError("Streaming receipt sequence has a gap or conflict")
        raw = (store.root / "raw" / d["source_hash"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != d["source_hash"]:
            raise ValueError("Streaming receipt envelope hash mismatch")
        value = json.loads(raw)
        if value["source_id"] != source_id or value["project_id"] != project_id or value["sequence"] != index:
            raise ValueError("Streaming receipt belongs to another source/project/sequence")
        wire = base64.b64decode(value["wire_base64"], validate=True)
        if hashlib.sha256(wire).hexdigest() != value["wire_sha256"]:
            raise ValueError("Original ETP wire hash mismatch")
        values.append(value)
    return values


def preserve(store, project_id, source_id, raw, session_id, *, event=None, mode="capture", received_at=None, direction="inbound"):
    source(store, project_id, source_id)
    UUID(session_id)
    if len(raw) > MAX_MESSAGE or mode not in {"capture", "historical_wire_replay", "synthetic_fixture"} or direction not in {"inbound", "outbound", "event"}:
        raise ValueError("Unsupported/beyond-limit capture")
    records = envelopes(store, project_id, source_id)
    if len(records) >= MAX_CAPTURES:
        raise ValueError("Capture capacity reached; start a separately identified source archive")
    receipt = received_at or now()
    timestamp(receipt)
    value = {"profile": PROFILE, "id": str(uuid4()), "project_id": project_id, "source_id": source_id,
             "sequence": len(records) + 1, "session_id": session_id, "received_at_utc": receipt,
             "receipt_basis": "adapter clock at WebSocket receipt" if mode == "capture" else "local replay/fixture ingestion clock",
             "mode": mode, "direction": direction, "wire_sha256": hashlib.sha256(raw).hexdigest(),
             "wire_base64": base64.b64encode(raw).decode("ascii"), "transport_event": event}
    encoded = canonical(value).encode("utf-8")
    return store.import_data(project_id, "etp_capture", "etp-receipt.json", encoded,
                             [{"capture_json": encoded.decode()}],
                             {"source_id": source_id, "sequence": value["sequence"], "received_at_utc": receipt,
                              "wire_sha256": value["wire_sha256"], "mode": mode, "profile": PROFILE}, [])


class ChannelState:
    def __init__(self, config):
        self.config = config
        self.bindings = {c.uri: c for c in config.channels}
        self.metadata = {}
        self.points = {}
        self.high_water = {}
        self.receipts = []
        self.last_change_time = 0
        self.last_server_time = None
        self.session_id = None
        self.last_message_id = -1
        self.transport = "not_connected"
        self.gaps = []
        self.multipart = {}
        self.read_ranges = {}

    def replay(self, records):
        for record in records:
            self.consume(record)
        return self

    def consume(self, record):
        # Decode again from original bytes; cached normalized JSON is not trusted.
        summary = {"sequence": record["sequence"], "received_at_utc": record["received_at_utc"],
                   "session_id": record["session_id"], "wire_sha256": record["wire_sha256"],
                   "mode": record["mode"], "status": "retained", "point_statuses": []}
        if record["session_id"] != self.session_id:
            if self.multipart:
                self.gaps.append("Incomplete multipart action at a session boundary")
            self.session_id = record["session_id"]
            self.last_message_id = -1
            self.metadata = {}
            self.multipart = {}
            self.read_ranges = {}
        try:
            if record["transport_event"] is not None:
                self.transport = record["transport_event"]
                summary["name"] = "TransportEvent"
                return summary
            message = decode(base64.b64decode(record["wire_base64"], validate=True))
            header, name, body = message["header"], message["name"], message["body"]
            summary.update(name=name, header=header)
            if record.get("direction") == "outbound":
                summary["status"] = "outbound_send_attempt"
                if name == "GetRanges":
                    self.read_ranges[header["messageId"]] = body["channelRanges"]
                return summary
            if header["messageId"] % 2 != 0 or header["messageId"] <= self.last_message_id:
                raise ValueError("Server message identity is duplicate or out of sequence in this session")
            self.last_message_id = header["messageId"]
            if name == "OpenSession":
                self.last_server_time = micros(body["currentDateTime"])
                earliest = micros(body["earliestRetainedChangeTime"])
                if self.last_change_time and earliest > self.last_change_time:
                    self.gaps.append("Server retained-change history no longer covers the previous checkpoint")
                self.transport = "session_open"
            elif name == "GetChannelMetadataResponse":
                before = dict(self.metadata)
                try:
                    for item in body["metadata"].values():
                        self.add_metadata(item)
                except (ValueError, KeyError, TypeError):
                    self.metadata = before
                    raise
            elif name in {"ChannelData", "GetRangesResponse", "RangeReplaced"}:
                key = (name, header["correlationId"] or header["messageId"])
                parts = self.multipart.setdefault(key, [])
                parts.append(body)
                if sum(len(b.get("data", [])) for b in parts) > MAX_POINTS:
                    raise ValueError("Multipart action exceeds the declared point limit")
                if header["messageFlags"] & 2:
                    parts = self.multipart.pop(key)
                    if name == "GetRangesResponse" and header["correlationId"] in self.read_ranges:
                        ranges = self.read_ranges.pop(header["correlationId"])
                        combined = [item for p in parts for item in p["data"]]
                        # The configured client requests one channel per action. Complete
                        # authoritative snapshots are applied only after FIN, not per fragment.
                        if len(ranges) != 1 or len(ranges[0]["channelIds"]) != 1:
                            raise ValueError("This profile requests one channel per GetRanges action")
                        replacement = {"changeTime": self.last_server_time or 0,
                                       "channelIds": ranges[0]["channelIds"],
                                       "changedInterval": ranges[0]["interval"], "data": combined}
                        summary["point_statuses"] = self.data_action("RangeReplaced", [replacement], record)
                    else:
                        summary["point_statuses"] = self.data_action(name, parts, record)
            elif name == "ChannelsTruncated":
                truncations = []
                for item in body["channels"]:
                    meta = self.metadata[item["channelId"]]
                    end = micros(item["newEndIndex"]["item"])
                    truncations.append((meta["uri"], end))
                change = micros(body["changeTime"])
                for uri, end in truncations:
                    self.points = {k: v for k, v in self.points.items() if k[0] != uri or k[1] <= end}
                    self.high_water[uri] = end
                self.last_change_time = max(self.last_change_time, change)
            elif name == "GetChangeAnnotationsResponse":
                # The client uses every interval for GetRanges recovery. Preserve response clocks,
                # but do not advance the durable change checkpoint before recovery completes.
                summary["changes"] = json_value(body)
            elif name == "SubscribeChannelsResponse":
                self.transport = "subscribed"
            elif name in {"Ping", "Pong"}:
                self.last_server_time = micros(body["currentDateTime"])
            elif name == "CloseSession":
                self.transport = "closed_by_server"
            elif name == "ProtocolException":
                self.transport = "protocol_error"
                summary["status"] = "quarantined"
                summary["reason"] = "Server returned a protocol error; original wire retained"
            elif name not in {"Acknowledge", "SubscriptionsStopped"}:
                raise ValueError("Unexpected message for the declared customer profile")
        except (ValueError, KeyError, TypeError) as error:
            summary["status"] = "quarantined"
            summary["reason"] = str(error)[:500]
        finally:
            self.receipts.append(summary)
        return summary

    def add_metadata(self, item):
        binding = self.bindings.get(channel_uri(item["uri"]))
        if not binding or item["uom"] != binding.unit or item["channelClassUri"] != binding.property_kind_uri:
            raise ValueError("Channel metadata does not match the explicit authorized quantity/unit/property binding")
        indexes = item["indexes"]
        if len(indexes) != 1 or indexes[0]["indexKind"] != "DateTime" or indexes[0]["uom"] != "us" or indexes[0]["direction"] != "Increasing":
            raise ValueError("This profile supports one increasing UTC DateTime index in microseconds")
        if item["dataKind"] not in {"typeDouble", "typeFloat", "typeLong", "typeInt"} or item["axisVectorLengths"]:
            raise ValueError("Only scalar numeric Channel objects are supported")
        if item["id"] < 0 or (item["id"] in self.metadata and self.metadata[item["id"]]["uri"] != item["uri"]):
            raise ValueError("Conflicting channel identity")
        self.metadata[item["id"]] = item

    def data_action(self, name, parts, record):
        # Validate the entire action before changing current values; incomplete replacement
        # actions cannot delete earlier evidence. Original receipts always remain immutable.
        points, previous = [], None
        order = {}
        for part in parts:
            for item in part["data"]:
                meta = self.metadata[item["channelId"]]
                if len(item["indexes"]) != 1:
                    raise ValueError("Unexpected secondary channel index")
                index = item["indexes"][0]["item"]
                index = previous if index is None else micros(index)
                if index is None:
                    raise ValueError("First data index cannot be elided")
                previous = index
                if item["channelId"] in order and index <= order[item["channelId"]]:
                    raise ValueError("Duplicate/out-of-order channel point within the same action")
                order[item["channelId"]] = index
                value = item["value"]["item"]
                if value is not None and (isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value)):
                    raise ValueError("Non-numeric/non-finite channel value")
                binding = self.bindings[meta["uri"]]
                points.append({"uri": meta["uri"], "source_time_us": index, "source_time_utc": iso(index),
                               "received_at_utc": record["received_at_utc"], "capture_sequence": record["sequence"],
                               "quantity": binding.quantity, "canonical_field": CANONICAL[binding.quantity],
                               "original_value": value, "original_unit": binding.unit,
                               "value_si": None if value is None else value * CHANNELS[binding.quantity][binding.unit],
                               "source": meta["source"], "attributes": json_value(item["valueAttributes"]),
                               "origin": self.config.origin, "wire_sha256": record["wire_sha256"]})
        replacements = []
        if name == "RangeReplaced":
            first = parts[0]
            if any(p["changedInterval"] != first["changedInterval"] or p["channelIds"] != first["channelIds"] for p in parts):
                raise ValueError("Multipart replacement range changed before FIN")
            interval = first["changedInterval"]
            if interval["uom"] != "us" or interval["depthDatum"]:
                raise ValueError("Replacement range must use the DateTime index units")
            start, end = interval["startIndex"]["item"], interval["endIndex"]["item"]
            start = micros(start) if start is not None else 0
            end = micros(end) if end is not None else 7258118400000000
            if start > end:
                raise ValueError("Replacement range is inverted")
            uris = {self.metadata[c]["uri"] for c in first["channelIds"]}
            if any(p["uri"] not in uris or not start <= p["source_time_us"] <= end or p["original_value"] is None for p in points):
                raise ValueError("Replacement data does not belong to its declared range")
            replacements = [(k, v) for k, v in self.points.items() if k[0] in uris and start <= k[1] <= end]
            change = micros(first["changeTime"])
        if len(self.points) - len(replacements) + len(points) > MAX_POINTS:
            raise ValueError("Current channel materialization exceeds the declared point capacity")
        for key, _ in replacements:
            self.points.pop(key)
        statuses = []
        for point in points:
            key = point["uri"], point["source_time_us"]
            old = self.points.get(key)
            status = "accepted"
            if old:
                comparable = ("original_value", "original_unit", "attributes", "source")
                if all(old[k] == point[k] for k in comparable):
                    status = "duplicate"
                else:
                    status = "conflicting_index"
                    old["quality"] = "withheld_conflict"
            elif name == "ChannelData" and point["source_time_us"] < self.high_water.get(point["uri"], -1):
                status = "out_of_order_quarantined"
            else:
                point["quality"] = "missing" if point["value_si"] is None else "observed"
                if point["attributes"]:
                    point["quality"] = "supplied_attributes_require_review"
                if timestamp(point["source_time_utc"]) > timestamp(record["received_at_utc"]) + timedelta(seconds=60):
                    point["quality"] = "source_clock_ahead"
                if point["value_si"] is not None and point["value_si"] < 0:
                    point["quality"] = "negative_observation"
                self.points[key] = point
                self.high_water[point["uri"]] = max(point["source_time_us"], self.high_water.get(point["uri"], -1))
            statuses.append({"uri": point["uri"], "source_time_us": point["source_time_us"], "status": status})
        if name == "RangeReplaced":
            self.last_change_time = max(self.last_change_time, change)
        return statuses

    def view(self, at=None):
        at = timestamp(at or now())
        receipts = [r for r in self.receipts if r["mode"] == "capture" and r["status"] != "quarantined" and r.get("name") == "ChannelData"]
        last_receipt = receipts[-1]["received_at_utc"] if receipts else None
        age = (at - timestamp(last_receipt)).total_seconds() if last_receipt else None
        stale = age is None or age < 0 or age > self.config.stale_after_s or self.transport != "subscribed"
        return {"profile": PROFILE, "transport": self.transport, "stale": stale,
                "last_live_data_received_at_utc": last_receipt, "receipt_age_s": age,
                "source_clock_utc": iso(self.last_server_time) if self.last_server_time is not None else None,
                "high_water_us": self.high_water, "last_change_time_us": self.last_change_time,
                "gaps": self.gaps, "pending_multipart_actions": len(self.multipart),
                "receipts": self.receipts, "points": sorted(self.points.values(), key=lambda p: (p["source_time_us"], p["uri"])),
                "equipment_control": False, "equipment_authority": "none",
                "independent_interoperability": "pending", "sampling_fabricated": False}


def materialize(store, project_id, source_id):
    return ChannelState(source(store, project_id, source_id)).replay(envelopes(store, project_id, source_id))
