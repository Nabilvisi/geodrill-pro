"""Schema-backed binary ETP messages. Customer output has an explicit allowlist."""
import io
import json
from functools import lru_cache
from pathlib import Path
from fastavro import parse_schema, schemaless_reader, schemaless_writer

SCHEMAS = Path(__file__).with_name("schemas")
MAX_MESSAGE = 1024 * 1024
READ_ONLY = {"RequestSession", "CloseSession", "Ping", "Pong", "Acknowledge",
             "ProtocolException", "GetChannelMetadata", "SubscribeChannels",
             "UnsubscribeChannels", "GetRanges", "GetChangeAnnotations", "GetDataObjects"}


@lru_cache(maxsize=32)
def schema(name):
    path = SCHEMAS / (name + ".avsc")
    if not path.is_file() or path.parent != SCHEMAS:
        raise ValueError("Unsupported ETP schema")
    return parse_schema(json.loads(path.read_text(encoding="utf-8")))


@lru_cache(maxsize=1)
def registry():
    records = {}
    for path in SCHEMAS.glob("*.avsc"):
        value = json.loads(path.read_text(encoding="utf-8"))
        if "protocol" in value:
            records[int(value["protocol"]), int(value["messageType"])] = value["name"]
    return records


def read_header(raw):
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_MESSAGE:
        raise ValueError("ETP message is not bounded binary data")
    stream = io.BytesIO(raw)
    try:
        header = schemaless_reader(stream, schema("MessageHeader"))
    except (EOFError, ValueError, OverflowError, IndexError) as error:
        raise ValueError("Invalid ETP header") from error
    if header["messageId"] < 0 or header["correlationId"] < 0:
        raise ValueError("Negative ETP message/correlation identity")
    if header["messageFlags"] & ~0x3a:
        raise ValueError("Unsupported ETP message flags")
    return header, stream


def decode(raw):
    header, stream = read_header(raw)
    if header["messageFlags"] & 0x08:
        raise ValueError("Compressed ETP bodies were not negotiated")
    key = header["protocol"], header["messageType"]
    name = registry().get(key)
    if name is None and header["messageType"] in (1000, 1001) and header["protocol"] in (0, 4, 21):
        name = "ProtocolException" if header["messageType"] == 1000 else "Acknowledge"
    if name is None:
        raise ValueError("ETP protocol/message is outside the declared read-only profile")
    extension = None
    try:
        if header["messageFlags"] & 0x20:
            extension = schemaless_reader(stream, schema("MessageHeaderExtension"))
        body = schemaless_reader(stream, schema(name))
    except (EOFError, ValueError, OverflowError, IndexError, TypeError) as error:
        raise ValueError("Invalid ETP schema body") from error
    if stream.read(1):
        raise ValueError("Trailing bytes after the ETP message")
    return {"header": header, "name": name, "body": body, "extension": extension}


def encode(name, body, message_id, correlation_id=0, flags=2, *, fixture=False, protocol=None):
    if not fixture and name not in READ_ONLY:
        raise ValueError("ETP customer may only emit declared read-only messages")
    selected = schema(name)
    header = {"protocol": int(selected.get("protocol", 0)) if protocol is None else protocol,
              "messageType": int(selected.get("messageType", 0)), "correlationId": correlation_id,
              "messageId": message_id, "messageFlags": flags}
    if not fixture and (message_id < 1 or message_id % 2 != 1 or flags & ~0x12):
        raise ValueError("Invalid ETP customer sequence or flags")
    stream = io.BytesIO()
    schemaless_writer(stream, schema("MessageHeader"), header)
    schemaless_writer(stream, selected, body)
    raw = stream.getvalue()
    if len(raw) > MAX_MESSAGE:
        raise ValueError("Encoded ETP message exceeds the declared limit")
    return raw
