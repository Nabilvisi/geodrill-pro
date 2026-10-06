"""Explicitly generated ETP schema fixtures; no field observations or server certification."""
import copy
from .wire import encode

CHANNEL_URI = "eml:///witsml21.Channel(01234567-89ab-4cde-8012-3456789abcde)"
PROPERTY_URI = "eml:///eml23.PropertyKind(12345678-9abc-4def-8012-3456789abcde)"
TIME_US = 1791288000000000


def configuration():
    return {"name": "Synthetic ETP protocol fixture", "endpoint": "ws://127.0.0.1:17765",
            "authorization_basis": "Generated software-verification transport; no rig or external store",
            "channels": [{"uri": CHANNEL_URI, "quantity": "spp", "unit": "MPa",
                          "property_kind_uri": PROPERTY_URI, "mapping_basis": "Generated pressure channel"}],
            "stale_after_s": 30., "origin": "synthetic", "loopback_fixture": True}


def metadata(channel_id=42, **patch):
    result = {"uri": CHANNEL_URI, "id": channel_id, "indexes": [{"indexKind": "DateTime",
              "interval": {"startIndex": {"item": TIME_US}, "endIndex": {"item": None}, "uom": "us", "depthDatum": ""},
              "direction": "Increasing", "name": "UTC time", "uom": "us", "depthDatum": "",
              "indexPropertyKindUri": "", "filterable": True}], "channelName": "Generated SPP",
              "dataKind": "typeDouble", "uom": "MPa", "depthDatum": "", "channelClassUri": PROPERTY_URI,
              "status": "Active", "source": "Synthetic schema fixture", "axisVectorLengths": [],
              "attributeMetadata": [], "customData": {}}
    result.update(patch)
    return result


def point(index=TIME_US, value=12., channel_id=42):
    return {"channelId": channel_id, "indexes": [{"item": index}], "value": {"item": value}, "valueAttributes": []}


def interval(start=TIME_US, end=TIME_US + 1000000):
    return {"startIndex": {"item": start}, "endIndex": {"item": end}, "uom": "us", "depthDatum": ""}


def generated_messages():
    """Metadata, accepted, duplicate, late, conflict, unsupported unit and repaired range."""
    bodies = [("GetChannelMetadataResponse", {"metadata": {"fixture": metadata()}}),
              ("ChannelData", {"data": [point()]}),
              ("ChannelData", {"data": [point()]}),
              ("ChannelData", {"data": [point(TIME_US-1000000, 10.)]}),
              ("ChannelData", {"data": [point(value=13.)]}),
              ("GetChannelMetadataResponse", {"metadata": {"bad": metadata(channel_id=43, uom="unknown")}}),
              ("RangeReplaced", {"changeTime": TIME_US+2000000, "channelIds": [42],
                                 "changedInterval": interval(), "data": [point(value=11.5)]})]
    return [encode(name, copy.deepcopy(body), 2*(index+1), fixture=True) for index, (name, body) in enumerate(bodies)]
