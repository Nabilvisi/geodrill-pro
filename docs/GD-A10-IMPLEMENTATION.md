# GD-A10 — directional research API

packages/engineering/directional.py provides coordinate conversion, survey uncertainty
and 3D closest approach through directional API routes. The pinned manifest declares
three ISCWSA diagnostic cases. tests/test_directional.py verifies coordinate round
trips, component comparisons, tie-ins/correlation assumptions and proximity edge cases.

These are API and numerical diagnostics. A dedicated integrated uncertainty/proximity
UI and field tool-run review remain open. The published FORGE trajectory reproduction
is separate evidence in evidence/SOURCE-PROVENANCE.md; it does not establish survey
measurement accuracy or validate a tool-error model.

clearance_generated remains false. No operational separation approval or equipment
command is provided.

