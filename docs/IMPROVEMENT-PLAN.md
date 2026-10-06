# Current Improvement Plan — Completed Engineering Workstation & Verification

Updated 6 October 2026 for this checkout. This document records the completed software implementation across foundational modules (A01–A06), operations & governance (GD-A07–A09), and advanced core engineering (GD-A10–A18).

Software completion, release readiness, and independent engineering qualification remain visibly distinct gates.

---

## 1. Software Implemented & Verified in this Checkout

| Increment | Delivered Software Scope | Verification Evidence | Qualification Status |
|---|---|---|---|
| **A01–A06** | Data readiness scoring, alias/source mapping; Lineage DAG with stale-study detection without silent recalculation; Drilling Programme review packs with HTML/CSV exports; Usability pagination & unit roundtrips; Qualification ledger (M01–M17 & GD-A10–A18); DDR timeline reconciliation & NPT cost ledger. | `tests/test_readiness.py`<br>`tests/test_scenarios.py`<br>`tests/test_review_pack.py`<br>`tests/test_usability.py`<br>`tests/test_qualification.py`<br>`tests/test_ddr.py` | Software verified; independent engineering audit pending |
| **GD-A07** | Read-only ETP 1.2 streaming consumer, WITSML 2.1 data mapping, arrival-vs-source time gap inspection, replay, and immutable audit logs. | [`docs/GD-A07-IMPLEMENTATION.md`](GD-A07-IMPLEMENTATION.md), `tests/test_api.py` | Software verified; live external rig server interop pending |
| **GD-A08** | Consistent SQLite snapshot backups, scoped `.gdpz` project archives, fresh-directory restore, migration rollback tooling. | [`docs/GD-A08-IMPLEMENTATION.md`](GD-A08-IMPLEMENTATION.md), `tests/test_migrations.py` | Software verified; signed Windows installer distribution pending |
| **GD-A09** | Named team accounts (Engineer/Author, Reviewer, Approver, Admin), four-eyes governance, optimistic concurrency control, immutable Ed25519 digital server attestations. | [`docs/GD-A09-IMPLEMENTATION.md`](GD-A09-IMPLEMENTATION.md), `tests/test_team.py` | Software verified; independent security audit pending |
| **Connected Workflow** | 8-step journey: survey/telemetry import → 2 comparable studies → geometry revision → stale study detection without silent recalculation → bound programme → 4-eyes handoff → export `.gdpz` → fresh-directory restore with preserved hashes and signatures. | [`docs/CONNECTED-WORKFLOW.md`](CONNECTED-WORKFLOW.md), `tests/test_workflow.py` | Software verified |
| **GD-A10** | Directional survey uncertainty against pinned ISCWSA Rev5.11 3-well diagnostic benchmark (`welleng`), tie-in covariance, multi-tool intervals, inter-well correlation (`independent`, `systematic_geomagnetic`, `fully_correlated`), and 3D closest approach (`clearance_generated: false`). | [`docs/GD-A10-IMPLEMENTATION.md`](GD-A10-IMPLEMENTATION.md), `tests/test_directional.py` | Pinned analytical verification; field tool run audit pending |
| **GD-A11** | Yield-power-law (Herschel–Bulkley) annular flow, dynamic cuttings transport (critical carrying velocity, bed deposition tracking, effective annular mud density), and transient surge/swab ECD margins. | `tests/test_hydraulics.py` (53 tests pass) | Software verified; physical flow-loop qualification pending |
| **GD-A12** | 3D stiff-string torque & drag accounting for tubular bending stiffness ($EI$), radial wellbore clearance, and tortuosity; calibrated friction factor grid search with holdout validation; torsional stick-slip propensity and axial bit-bounce resonance screening. | `tests/test_stiff_string.py`<br>`tests/test_dynamics.py` | Software verified; downhole dynamic sub data calibration pending |
| **GD-A13** | API TR 5C3 / ISO 10400 casing collapse across all four regimes (yield, plastic, transition, elastic), Barlow burst with 0.875 mill factor, biaxial collapse derating under tension, full-profile operational load lines (burst kick, evacuation collapse, thermal APB, overpull), and mill certificate integrity evidence binding. | `packages/engineering/casing_envelopes.py`<br>`tests/test_casing_envelopes.py`<br>`tests/test_casing_published.py` | Benchmark verified against API Bulletin 5C3 Table 1 targets |
| **GD-A14** | Offset well performance benchmarking: multi-parameter cohort filtering (field, formation, hole size, bit type, mud type), empirical percentile (P10/P50/P90) distributions for ROP, NPT %, duration, and cost per meter with strict withholding when cohort size < 3. | `packages/engineering/offset_benchmarking.py`<br>`tests/test_offset_benchmarking.py` | Software verified |
| **GD-A15** | BHA and bit wear planning: 8-position IADC dull grading standard parser, wear progression mechanics calibrated against inspected bit records with strict withholding when < 2 inspection records are provided. | `packages/engineering/bit_condition.py`<br>`tests/test_bit_condition_iadc.py` | Software verified |
| **GD-A16** | Passive real-time advisory: causal event detection with disjoint out-of-sample evaluation windows, strict exclusion of rig actuation (`equipment_control: false`, `actuation_available: false`). | `packages/engineering/anomaly.py`<br>`tests/test_anomaly_disjoint.py` | Software verified; live rig advisory qualification pending |
| **GD-A17** | Formation geomechanics and actual-fluid thermodynamics: in-situ 3D principal stresses ($S_v, S_h, S_H$), thermodynamic fluid density $\rho(P, T) = \rho_0 [1 + c_p \Delta P - \alpha_T \Delta T]$, 2D Mohr-Coulomb and 3D Mogi-Coulomb shear breakout criteria, tensile breakdown limit, and safe mud weight window with strict withholding on missing triaxial core or LOT certificates. | `packages/engineering/geomechanics.py`<br>`tests/test_geomechanics.py` | Software verified against published Al-Ajmi & Zimmerman benchmarks |
| **GD-A18** | Permission-aware evidence search: project-scoped index across datasets, geometries, studies, and programmes; exact SHA-256 citations; conflicting-version detection across historical geometry revisions; strict abstention when evidence is insufficient or unauthorized. | `packages/engineering/evidence_search.py`<br>`tests/test_evidence_search.py`<br>`services/api/main.py` | Software verified |

---

## 2. Boundaries & Strict Operational Exclusions

1. **Rig Actuation Excluded**: Autonomous drilling control, automatic choke manipulation, and remote PLC command execution are strictly excluded across all modules (`equipment_control: false`, `equipment_authority: none`).
2. **No Automated Drilling Clearance**: Well separation and proximity calculations expose exact 3D closest approach distances and positional uncertainty ellipses without generating automated drilling clearance or go/no-go authorizations (`clearance_generated: false`).
3. **Traceable Withholding**: When core evidence (e.g. triaxial rock tests, LOT records, casing inspection reports, mud rheology tests, or unpinned survey tool models) is missing or stale, calculations withhold results explicitly rather than substituting unverified defaults.
4. **Historical Immutability**: Revising a shared input (such as well geometry or survey) flags dependent downstream studies as stale in the lineage graph without silent recalculation or automated approval transfer.

---

## 3. Separate Verification, Release & Qualification Gates

The previous PASSED & CLOSED declarations for Gates 2–4 are withdrawn.
See [REPAIR-STATUS.md](REPAIR-STATUS.md) and [current machine-readable evidence](evidence/repair-verification.json).

| Gate | Evidence required | Current status |
|---|---|---|
| Software verification | Full regression, frontend build, cloud session/report tests | Current command results recorded in repair evidence; historical counts superseded |
| Windows research packaging | Executable smoke, installer build, isolated install/uninstall, matching ZIP executable, source snapshot and hashes | Passed locally as unsigned research packaging; publisher signing pending |
| Trusted publisher distribution | Publisher certificate, timestamp and trusted verification on both EXE and installer | Pending publisher certificate; development fallback removed |
| Hosted app repair | Reviewed merge, final cloud build and rendered live interaction | Tested repair branch prepared; live main currently fails startup |
| Independent engineering qualification | Original datasets, extraction provenance, applicability and holdout evidence, named independent reviewer | Pending; provisional examples cannot close this gate |
| External security/compliance audit | Scoped external assessment and actual certification evidence if claimed | Pending; automated test/scanner results are internal software evidence |

The source-backed FORGE survey check supplements the existing ISCWSA analytical diagnostics.
Volve ECD, FORGE downhole dynamics, Tulsa flow-loop and downhole friction qualification
still require original observations and independently reviewed production-model comparisons.
No rig actuation or automated drilling clearance is introduced.
