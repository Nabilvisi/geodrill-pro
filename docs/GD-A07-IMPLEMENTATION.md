# GD-A07 — streaming adapter remains unimplemented

The earlier delivered declaration is withdrawn. services/api/main.py exposes bounded
file imports and historical source-time replay. No ETP session negotiation, WITSML
object decoder, channel subscription, reconnect state or arrival-time store was found.
Installing XML/WebSocket dependencies does not implement this adapter. DDR XML export
is a custom interchange document, not proof of WITSML 2.1 schema conformance.

The acceptance requirements remain in [the original backlog](research/post-module-17/BACKLOG.md):
an isolated read-only adapter, an authorized source, original bytes and receipt/source
times, deduplication, ordering/reconnect handling, quarantine, stale-state display,
supported-object declarations, fixtures and independent server/soak evidence.
No equipment command protocol belongs in this work.

This is unfinished software scope. Authorized external server access is additionally
required for interoperability qualification.

