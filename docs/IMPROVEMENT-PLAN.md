# Current improvement plan — connected workflow and GD-A10

Updated 5 October 2026 for this checkout. This document is the current implementation plan; the original post-Module-17 research remains a historical proposal. The uploaded Windows progress document is reference material, not proof that its files or release exist here. The [Improvement Task](thread://01a10bdf-14c4-7f52-a8c1-4269cc2ee1e6?hostId=local) informed the foundation-first ordering.

## Software implemented in this checkout

| Increment | Delivered software | Verification evidence | Gates still open |
|---|---|---|---|
| GD-A07 | Restricted read-only ETP 1.2 capture/consumer, WITSML 2.1 mappings, reconciliation, replay and reports | [Implementation](GD-A07-IMPLEMENTATION.md), exchange tests and browser evidence in [verification](VERIFICATION.md) | Authorized external-server interoperability and field qualification |
| GD-A08 | Consistent verified backups, scoped `.gdpz` projects, fresh-directory restore, migration backup and rollback tooling | [Implementation](GD-A08-IMPLEMENTATION.md), recovery tests and browser evidence in [verification](VERIFICATION.md) | Fresh Windows install/update/rollback, signed packaging |
| GD-A09 | Named team accounts, membership, independent author/reviewer/approver, optimistic conflicts, immutable Ed25519 server attestations | [Implementation](GD-A09-IMPLEMENTATION.md), role/signature/conflict tests and browser evidence in [verification](VERIFICATION.md) | Independent security review and shared deployment qualification; signatures are server attestations, not personal certificates |
| Connected workflow | Workflow-specific readiness; exact dependency explanations; recursive stale-study detection; searchable study records; input/result comparison; programme evidence picker and exact binding validation; exported explanations | [Workflow implementation and journey](CONNECTED-WORKFLOW.md), `tests/test_workflow.py` | Remaining A01–A06 capabilities below |
| GD-A10 staged research | Explicit local/WGS84 UTM references and tie-ins; independent coordinate cases; single-tool ISCWSA MWD Rev5.11 propagation against pinned three-well diagnostics; supplied-covariance preservation; bounded multiwell closest approach; path inspection and reproducible reports | [GD-A10 implementation](GD-A10-IMPLEMENTATION.md), `tests/test_directional.py`, [pinned manifest](../packages/engineering/directional_cases/manifest.json) | Mixed tools, nonzero tie-in propagation, inter-well correlation, broader geodesy and specialist qualification |
| GD-A11 | Yield-power-law (Herschel-Bulkley) annular flow, dynamic cuttings transport (critical velocity, bed deposition, annular loading), transient surge/swab ECD margins | `tests/test_hydraulics.py`, `tests/test_research_modules.py` | Full-scale loop validation, thermal variations, dynamic wellbore instability |
| GD-A12 | 3D stiff-string torque & drag with tubular stiffness and radial clearance; fundamental vibration screening (torsional stick-slip, axial bit-bounce); preservation of soft-string baseline | `tests/test_stiff_string.py`, `tests/test_dynamics.py` | Calibration with physical dynamic sub data, lateral resonance modeling |
| GD-A13 | API TR 5C3 / ISO 10400 collapse (four regimes), Barlow/Lamé burst, biaxial reduction, 4 operational load-line profiles (burst kick, evacuation, thermal APB, overpull), mill test & pressure test integrity binding | `packages/engineering/casing_envelopes.py`, `tests/test_casing_envelopes.py` | Full-string connection seal qualification, non-uniform local wear grooves, elastoplastic burst |

No automatic recalculation, approval transfer or drilling clearance is generated. A new geometry revision flags historical dependent studies. Existing results, reports, programme content and signatures remain attached to the original evidence. A new bound programme cannot start or advance review with stale or unresolved study references. Unlinked older programmes remain readable and are explicitly labelled.

## A01–A06 reconciliation

The uploaded roadmap cites `readiness.py`, `scenarios.py`, `review_pack.py`, `usability.py`, `qualification.py`, `ddr.py` and matching tests; those claimed implementations are absent from this checkout. Existing unit-bound imports and M1–M17 research modules are not evidence of their completion.

| Item | Current subset | Missing scope |
|---|---|---|
| A01 | Explicit import units, immutable sources, selected-workflow missing-input checks | Versioned alias/source mapping, completeness scoring, bulk quarantine and large streaming imports |
| A02 | Exact identities, recursive dependencies, geometry-head staleness, comparisons | Named scenario bundles and a shared revisioned mud/input catalogue; independent supporting imports are not assumed to replace each other |
| A03 | Signed immutable programmes, exact study/source bindings, complete fixed JSON reports and recovery bundles | Structured section/activity/hazard register and complete human-readable HTML/PDF/CSV review pack |
| A04 | Searchable project study records, exact inspection, mobile navigation and directional chart cursor | Large-record pagination, all-module unit profiles/roundtrips and full keyboard/error-jump workflows |
| A05 | Pinned GD-A10 diagnostic gate and recorded module benchmark tests | Cross-model qualification ledger with independent evidence, reviewers, expiry and release gates |
| A06 | Existing source-time telemetry replay | DDR daily interval reconciliation, NPT adjudication, budget/actual cost ledger and qualified exchange |

## Current increment acceptance

The verified journey imports survey and supporting data, saves geometry and two comparable studies, changes the shared geometry, identifies dependent historical studies, saves a current study, binds a programme, completes independent author/reviewer/approver/issuer handoff, exports a report/project bundle, restores into a new directory and verifies identical content hashes and signed evidence. Tests also cover missing inputs, stale saves, revoked project access, incompatible references and corrupted bundles.

Desktop, phone and locally hosted Streamlit use the packaged frontend and the same Python API. This establishes local behavior only. It does not establish that the public Streamlit installation or a downloaded Windows executable contains this increment.

## Remaining sequence

1. Finish the outstanding A01–A06 foundation scopes above, prioritizing a revisioned shared-input catalogue, complete readable review exports and a qualification ledger. Keep the current connected workflow intact.
2. Extend GD-A10 only with independently pinned coordinate and tool/interval/correlation cases. Never substitute generic ellipses for an ISCWSA model.
3. **A11 — advanced hydraulics:** select closures with reproducible pressure-loss/thermal/compressibility cases and declared ranges. Existing M6 Newtonian, Bingham and Herschel–Bulkley laminar tests support that kernel only; they do not qualify turbulent, transient, multiphase or thermal extensions.
4. **A12 — calibrated torque/drag and contact:** require observed load histories, separate calibration/holdout wells and independently benchmarked contact assumptions. Existing soft-string analytical cases do not establish calibrated stiff-string accuracy.
5. **A13 — integrity evidence:** bind installed/as-built, inspection/test/expiry records and independent casing solver cases. Existing supplied body/connection ratings and Lamé checks do not establish full integrity qualification.
6. **A14 — offset programme/duration/cost:** require comparable cohorts and adjudicated DDR/NPT/cost records; disclose cohort selection and uncertainty.
7. **A15 — BHA/bit/wear planning:** require characterized materials, inspected histories and held-out benchmark cases.
8. **A16 — passive event intelligence:** require independent event adjudication, source availability times, disjoint evaluation and authorized passive deployment.
9. **A17 — actual-fluid thermodynamics and formation geomechanics:** restored to the sequence; require characterized composition/PVT, thermophysical data, formation properties and independent cases. Existing M16 supplied/reduced scenarios are not this capability.
10. **A18 — permission-aware evidence search:** extend the implemented project-scoped exact-record search to document/page citations and evidence-supported answers; abstain when records cannot support the answer. Preserve access checks and revision hashes throughout.

These extensions remain future work where their benchmark inputs are unavailable. Autonomous rig control (A19), equipment writes and automatic drilling authorization remain excluded.

## Separate release and qualification gates

- **Software completion:** automated evidence, production/Streamlit packaging and local browser checks for the selected implemented scope.
- **Release readiness:** fresh Windows packaging/install/update/recovery, signing and exact build verification; shared deployment hardening, operational monitoring and deployment smoke tests. Pending.
- **Engineering/security qualification:** independent specialist and security reviews, applicable standards, operator acceptance and external benchmark/field evidence. Pending.

Passing software tests does not close either of the latter gates. No deployment or Windows-release equivalence is inferred from the version string.
