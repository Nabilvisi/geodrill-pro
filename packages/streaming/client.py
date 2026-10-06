"""Isolated read-only WebSocket customer. Credentials exist only in process memory.

The API never starts outbound connections. Run this client separately against a
specifically configured and authorized store. TLS verification cannot be disabled.
"""
import asyncio
import base64
import time
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
from filelock import FileLock
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidHandshake
from .capture import materialize, source, preserve, envelopes, micros, PROFILE
from .wire import decode, encode, read_header, MAX_MESSAGE


def clock_us():
    return int(datetime.now(timezone.utc).timestamp() * 1000000)


class ReadOnlyClient:
    def __init__(self, store, project_id, source_id, *, bearer_token=None):
        self.store, self.project_id, self.source_id = store, project_id, source_id
        self.config = source(store, project_id, source_id)
        if not self.config.loopback_fixture and not bearer_token:
            raise ValueError("Authorized production store requires an in-memory bearer token")
        if bearer_token and any(c in bearer_token for c in "\r\n"):
            raise ValueError("Invalid bearer token")
        self.bearer_token = bearer_token
        self.state = materialize(store, project_id, source_id)
        self.session_id = None
        self.message_id = 1
        self.pending_ranges = set()
        self.pending_metadata = {}
        self.subscribed = False
        self.stats = {"connections": 0, "inbound_messages": 0, "quarantined": 0,
                      "outbound_messages": 0, "profile": PROFILE, "equipment_control": False}

    async def retain(self, raw=b"", *, event=None, direction="inbound", received_at=None):
        await asyncio.to_thread(preserve, self.store, self.project_id, self.source_id, raw,
                                self.session_id, event=event, direction=direction, received_at=received_at)
        # The final original envelope is replayed through the same parser as reports/API reads.
        # Single-writer exclusion below keeps receipt identities and session state stable.
        record = (await asyncio.to_thread(envelopes, self.store, self.project_id, self.source_id))[-1]
        return self.state.consume(record)

    async def send(self, ws, name, body, *, correlation=0, protocol=None):
        mid = self.message_id
        self.message_id += 2
        raw = encode(name, body, mid, correlation, protocol=protocol)
        await self.retain(raw, direction="outbound")
        await ws.send(raw)
        self.stats["outbound_messages"] += 1
        return mid

    async def subscribe(self, ws):
        channels = {str(m["id"]): {"channelId": m["id"],
                    "startIndex": {"item": self.state.high_water.get(m["uri"])},
                    "dataChanges": True, "requestLatestIndexCount": None}
                    for m in self.state.metadata.values()}
        if not channels or len(channels) != len(self.config.channels):
            raise ValueError("All configured channels must have compatible metadata before subscribing")
        await self.send(ws, "SubscribeChannels", {"channels": channels})
        self.subscribed = True
        # Obtain changes since the pre-read session clock to expose changes during synchronization.
        await self.send(ws, "GetChangeAnnotations", {"channels": {"checkpoint": {
            "sinceChangeTime": self.change_anchor, "channelIds": sorted(self.state.metadata)}}, "latestOnly": False})

    async def receive(self, ws, raw):
        received_at = datetime.now(timezone.utc).isoformat()
        self.stats["inbound_messages"] += 1
        try:
            header, _ = read_header(raw)
            if header["messageFlags"] & 0x10 and header["messageType"] != 1001:
                # Acknowledge precedes body/extension deserialization as required by ETP.
                await self.send(ws, "Acknowledge", {}, correlation=header["messageId"], protocol=header["protocol"])
        except ValueError:
            summary = await self.retain(raw, received_at=received_at)
            self.stats["quarantined"] += 1
            return summary
        summary = await self.retain(raw, received_at=received_at)
        if summary["status"] == "quarantined":
            self.stats["quarantined"] += 1
            await self.send(ws, "ProtocolException", {"error": {"code": 19, "message": "Message outside declared customer profile; original bytes retained"}, "errors": {}}, correlation=header["messageId"])
            return summary
        message = decode(raw)
        name, body = message["name"], message["body"]
        if name == "OpenSession":
            protocols = {int(p["protocol"]): p for p in body["supportedProtocols"]}
            selected = protocols.get(21)
            if not selected or selected["role"] != "store" or selected["protocolVersion"] != {"major": 1, "minor": 2, "revision": 0, "patch": 0}:
                raise ValueError("Peer did not negotiate the required ETP 1.2 ChannelSubscribe store role")
            objects = {v["dataObjectType"] for v in body["supportedDataObjects"]}
            if not (objects & {"witsml21.Channel", "witsml21.*", "*"}) or body["supportedCompression"]:
                raise ValueError("Peer did not negotiate WITSML 2.1 Channel objects/uncompressed bodies")
            self.change_anchor = micros(body["currentDateTime"])
            await self.send(ws, "GetChannelMetadata", {"uris": {str(i): c.uri for i, c in enumerate(self.config.channels)}})
        elif name == "GetChannelMetadataResponse":
            if header["messageFlags"] & 2:
                if len(self.state.metadata) != len(self.config.channels):
                    raise ValueError("Peer omitted configured channel metadata")
                # Full authoritative reads also recover earlier edits, deletions and gaps.
                # This deliberately avoids claiming that source-index replay alone recovers changes.
                for cid in sorted(self.state.metadata):
                    mid = await self.send(ws, "GetRanges", {"requestUuid": uuid4().bytes,
                        "channelRanges": [{"channelIds": [cid], "interval": {
                            "startIndex": {"item": None}, "endIndex": {"item": None},
                            "uom": "us", "depthDatum": ""}, "secondaryIntervals": []}]})
                    self.pending_ranges.add(mid)
        elif name == "GetRangesResponse":
            if header["messageFlags"] & 2:
                self.pending_ranges.discard(header["correlationId"])
                if not self.pending_ranges and not self.subscribed:
                    await self.subscribe(ws)
        elif name == "GetChangeAnnotationsResponse":
            for info in body["changes"].values():
                for channel, changes in info["changes"].items():
                    cid = int(channel)
                    if cid not in self.state.metadata:
                        raise ValueError("Change annotation references an unrequested channel")
                    for change in changes:
                        if change["interval"]["uom"] != "us" or change["interval"]["depthDatum"]:
                            raise ValueError("Change annotation uses incompatible index units")
                        mid = await self.send(ws, "GetRanges", {"requestUuid": uuid4().bytes,
                            "channelRanges": [{"channelIds": [cid], "interval": change["interval"], "secondaryIntervals": []}]})
                        self.pending_ranges.add(mid)
        elif name == "Ping":
            await self.send(ws, "Pong", {"currentDateTime": clock_us()}, correlation=header["messageId"])
        elif name == "CloseSession":
            raise ConnectionError("Peer closed the ETP session")
        return summary

    async def run(self, *, duration_s=None, max_messages=None, max_reconnects=8, reconnect_delay_s=.25):
        lock_dir = self.store.root / "adapter-locks"
        lock_dir.mkdir(exist_ok=True)
        lock = FileLock(str(lock_dir / (self.source_id + ".active.lock")), timeout=0)
        deadline = time.monotonic() + duration_s if duration_s is not None else float("inf")
        with lock:
            reconnects = 0
            while time.monotonic() < deadline and (max_messages is None or self.stats["inbound_messages"] < max_messages):
                self.session_id = str(uuid4())
                self.message_id = 1
                self.pending_ranges = set()
                self.subscribed = False
                await self.retain(event="connecting", direction="event")
                headers = {"etp-encoding": "binary"}
                if self.bearer_token:
                    headers["Authorization"] = "Bearer " + self.bearer_token
                try:
                    async with connect(self.config.endpoint, subprotocols=["etp12.energistics.org"],
                            additional_headers=headers, compression=None, max_size=MAX_MESSAGE,
                            max_queue=16, open_timeout=10, close_timeout=2, proxy=None) as ws:
                        if ws.subprotocol != "etp12.energistics.org":
                            raise ValueError("WebSocket peer did not select ETP 1.2")
                        self.stats["connections"] += 1
                        await self.send(ws, "RequestSession", {"applicationName": "GeoDrill Pro read-only customer",
                            "applicationVersion": "0.8.0", "clientInstanceId": uuid4().bytes,
                            "requestedProtocols": [{"protocol": 21, "protocolVersion": {"major": 1, "minor": 2, "revision": 0, "patch": 0},
                                                    "role": "store", "protocolCapabilities": {}}],
                            "supportedDataObjects": [{"qualifiedType": "witsml21.Channel", "dataObjectCapabilities": {}}],
                            "supportedCompression": [], "supportedFormats": ["xml"], "currentDateTime": clock_us(),
                            "earliestRetainedChangeTime": 0, "serverAuthorizationRequired": False,
                            "endpointCapabilities": {"MaxWebSocketMessagePayloadSize": {"item": MAX_MESSAGE}}})
                        while time.monotonic() < deadline and (max_messages is None or self.stats["inbound_messages"] < max_messages):
                            timeout = min(15., max(.001, deadline - time.monotonic()))
                            try:
                                raw = await asyncio.wait_for(ws.recv(), timeout)
                            except asyncio.TimeoutError:
                                if time.monotonic() < deadline:
                                    await self.send(ws, "Ping", {"currentDateTime": clock_us()})
                                continue
                            if isinstance(raw, str):
                                await self.retain(raw.encode("utf-8"), received_at=datetime.now(timezone.utc).isoformat())
                                self.stats["quarantined"] += 1
                                continue
                            await self.receive(ws, raw)
                        await self.send(ws, "CloseSession", {"reason": "Bounded read-only capture completed"})
                        break
                except (ConnectionClosed, ConnectionError, OSError, InvalidHandshake):
                    await self.retain(event="disconnected", direction="event")
                    if reconnects >= max_reconnects:
                        break
                    reconnects += 1
                    await self.retain(event="reconnecting", direction="event")
                    await asyncio.sleep(min(reconnect_delay_s * 2**min(reconnects-1, 5), max(0., deadline-time.monotonic())))
                except ValueError:
                    await self.retain(event="fatal_protocol_error", direction="event")
                    raise
            await self.retain(event="stopped", direction="event")
        return {**self.stats, "reconnects": reconnects, "stopped": True}
