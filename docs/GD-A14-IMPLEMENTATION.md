# GD-A14 — connected offset cohort workflow

Offset benchmarks is available in the workstation navigation. Save immutable M1
geometry, select the project and geometry revision, then import complete typed SI
JSON or edit the draft. Original imported bytes, SHA-256 and normalized document
are preserved. Study input edits retain the original document and record whether
the saved inputs match it. The schema is supplied by /api/research/schemas.

Routes use the existing project membership, role and request-size boundaries:

- GET /api/projects/{project_id}/research/offset-benchmarking/template/{revision_id}
- POST /api/projects/{project_id}/research/offset-benchmarking/imports
- POST /api/projects/{project_id}/calculations/offset-benchmarking

The result retains included and excluded wells, filtering reasons, supplied
adjudication notes and per-record source hashes. Currencies are never silently
pooled or converted. Unknown evidence or fewer than three eligible records
withholds projections. Draft examples exist only in synthetic projects; other
projects start with an empty cohort and unknown evidence.

Model GD-A14-offset-benchmarking-2 reports empirical quantiles, not forecast
probabilities or confidence intervals. ROP favorable P10 uses the 90th percentile
of speed; low-duration/low-cost favorable P10 uses the 10th percentile. Planned
duration and historical total cost scale each original observation before
computing quantiles. Rig-time cost multiplies unrounded duration by the supplied
daily rate as a separate scenario; it is never added to historical total cost.
P50 is labeled median. Small positive lower input bounds prevent numerical
overflow from effectively zero durations/intervals.

Saved studies reopen, appear in fixed reports and survive signed project archive
restore through calculation.restored audit records. Evidence search cites the
complete calculation hash separately from geometry and original-file hashes.
The Streamlit synthetic workspace seeds a preserved offset document and study.

Tests cover hand-computed quantiles, rate changes, currency exclusion, unknown
evidence, original-file/edit provenance, geometry/datum/project failures, read-only
roles, membership, report snapshots, restart and archive restoration.

Remaining acceptance: real harmonized DDR cohorts, actual independent NPT
adjudication, currency/vintage/scope handling if needed, representative operator
acceptance and prospective holdout qualification. Supplied adjudication fields
and hashes are assertions; the application does not verify unseen original DDRs.
No budget commitment, drilling clearance or equipment authority is issued.
