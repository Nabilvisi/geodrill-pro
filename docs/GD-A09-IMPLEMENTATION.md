# GD-A09 — local team API and revision attestations

services/api/auth.py, access.py, team.py and programmes.py implement admin, engineer,
reviewer, approver and viewer accounts. The engineer acts as programme author.
Passwords use scrypt; sessions use random opaque tokens with token SHA-256 stored.
This is not JWT/OAuth issuance.

The API checks project membership, author/reviewer separation, version conflicts and
programme transitions. Ed25519 server attestations bind exact content, actor,
transition, time and predecessor. They identify a server key and recorded actor;
they are not individual certificate signatures or independent engineering approvals.
Imported keys are supplied trust. Team identity-bearing project restore is admin-only.

The cloud demo uses separate temporary browser-session workspaces and does not
provide shared team collaboration. A dedicated team sign-in/workflow interface and
hardened shared network deployment are not established by API tests.

Evidence: tests/test_team.py, test_workflow.py, test_security_audit.py and
test_project_recovery.py. External review, key custody, organizational controls and
operator acceptance remain open.

