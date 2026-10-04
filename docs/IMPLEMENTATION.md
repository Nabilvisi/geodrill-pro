# Implementation record — current version 0.8.0

The audited research software build is complete through Module 17. Modules 1–11 retain their existing inputs, studies, sources and historical reports. Six new geometry-bound workflows add reduced coupled BHA response/native sensor review, recovered-bit cohorts, separate casing wear/fatigue, causal flow/stock balance replay, characterized or externally reviewed phase studies, and an isolated pressure-plant/PID/request-validator simulation.

Typed SI contracts, engineering-unit editors, complete original JSON import/export, source hashes, canonical Parquet documents, plots/tables, saved-study reopening and fixed report inclusion are connected throughout. Unknown/unsupported evidence preserves a withholding reason. No physical sensor inference, individual-life recommendation, actual-mud solubility solver or rig-control adapter is claimed.

All 406 automated tests pass, including 102 new cases. TypeScript and the final production build pass. Actual Chrome verification covers six imported/saved workflows, successful and withheld cases, fixed report download, exact reopening after the real launcher restart and desktop/mobile rendering. Served asset bytes, original source hashes, five fixed reports and the 110-entry local audit chain verify.

Scope: [MODULES-1-17.md](MODULES-1-17.md). Numerical contracts: [MODEL-SPECS-0.8.md](MODEL-SPECS-0.8.md). Final outcomes: [VERIFICATION.md](VERIFICATION.md). Additional instrument/material/fluid/field/OEM evidence remains a qualification requirement. The release has equipment_control=false and equipment_authority=none.

---

# Prior Module 11 milestone / version 0.7.0

Module 11 is connected to the existing M1 geometry and M10 load workflows. It implements named straight-inclined confined-pipe sinusoidal/helical screens, effective-force conventions, local load uncertainty, and an optional conditional helical axial-drag equilibrium. Unsupported contact configurations, curved/vertical intervals, rotating/torqued sources and end restraints remain explicit saved withholding states.

The typed research editor now supports a same-geometry torque/drag source selector, engineering units, material/boundary provenance, local susceptibility indicators, conservative margins, depth plots, conditional transfer plots and immutable study reopening. All studies preserve geometry/survey/source hashes and appear in fixed reports. Version metadata is consistent across frontend, API and reports. No new runtime dependency or equipment endpoint was added.

Numerical scope: MODEL-SPECS-0.7.md. Requirement-by-requirement completion audit: MODULES-1-11.md. The release passes 304 tests plus TypeScript/build and Chrome workflow, restart, report, mobile and live-asset verification. Independent laboratory/field qualification and general 3D nonlinear beam/contact remain open production requirements.

# Prior Modules 7–10 milestone / version 0.6.0

# Implementation record — current version 0.6.0

The research build through Module 10 is implemented. M7 adds geometry-oriented elastic/thermal wall-stress scenarios; M8 binds saved M6 Newtonian properties to a conserved dilute vertical solids inventory; M9 adds an offline finite-volume acoustic displacement transient with three-grid/time checks; M10 adds soft-string torque/drag separately from MSE. Input contracts, source ownership/datum/integrity checks, immutable calculations and report inclusion apply to all new studies.

A reusable schema-driven React editor renders typed engineering fields, motion/string records, evidence states and hydraulic-source selection. Result views include stress/load/pressure/transport plots, time histories, meaningful withheld/incomplete conditions, numerical diagnostics and saved-study reopening. Supplied evidence resets when assumptions change. Historical projects cannot claim generated synthetic inputs. No third-party runtime dependency, cloud or equipment endpoint was added.

The numerical specification is MODEL-SPECS-0.6.md; delivery scope is MODULES-1-10.md; current verification is VERIFICATION.md. Unsupported coupled rock, bed transport and full trip hydrodynamics remain explicitly unavailable, and no field accuracy or operating approval is claimed.

# Prior Module 6 milestone / version 0.5.0


M6 adds steady laminar Newtonian, Bingham and Herschel–Bulkley circulation against immutable M1 geometry. Pipe flow uses a yielded radial integral; concentric annulus flow solves two no-slip boundaries with separate yielded domains and quadrature refinement. Pressure head uses TVD, friction uses MD, and continuous margin extrema are checked within minimum-curvature arcs. Mud age, supplied pressure-window review state, missing equipment ratings, failed corners and unsupported regimes remain explicit.

Surface supply, standpipe and bottom nozzle references are distinct. Profiles, segment diagnostics, corner parameters and source/revision hashes persist in fixed reports. The UI resets window review state after knot edits and preserves original results after later edits. Fifty-two new tests pass; the full suite is 200. See MODEL-SPECS-0.5.md and VERIFICATION.md for evidence and limits.

The original single-point balance remains available in Engineering lab. Its historical explanation below describes that older subset, not the new M6 profile solver.

# Prior Module 5 milestone / version 0.4.0

M5 now implements the audit's imported vendor-result review scope. Strict JSON source imports preserve supplied instrument/model metadata, native samples, timestamps, intervals and quality; source/revision integrity is checked before aligned-depth review. Scatter/range plots, withheld states, fixed reports and saved studies have been exercised in Chrome. Native EM inversion remains unavailable. Thirty new automated cases pass; the full suite is 148 tests. See MODEL-SPECS-0.4.md.

## Prior Module 4 milestone / version 0.3.0

M4 now implements the selected wet-shale Thomas–Stieber volume model, native-log interpretation scenarios, explicit coexisting-texture ambiguity, endpoint/observation sensitivity and two porosity crossplots. Source-specific correction evidence resets on log changes. The source library refreshes when entered after a module adds an example. See MODEL-SPECS-0.3.md for the exact convention; no apparent sonic/neutron response conversion or geological acceptance is inferred.

The original M1–M3 continuation record follows.

## Continuation on 3 October 2026

The relocated installation is at C:\Users\HP\OneDrive\Project Drill\geodrill-pro. Version 0.2.0 extends the existing projects with immutable M1 geometry revisions, a 3D editor and exact formation intersections, M2 restricted casing evidence/load screens and M3 exploratory native-depth log clustering. No data was recreated or replaced.

Engineering revisions and calculation records reject ordinary SQLite updates/deletes. New fixed reports use schema 1.1 and include revisions. Existing reports remain unchanged. The local session and equipment boundary are retained.

See [MODEL-SPECS-0.2.md](MODEL-SPECS-0.2.md) for equations and assumptions, [MODULES-1-10.md](MODULES-1-10.md) for the full active delivery objective, and [VERIFICATION.md](VERIFICATION.md) for current evidence. The research scope remains conditional on supplied evidence. No field qualification or design approval is issued.

The notes below preserve the original 0.1.0 implementation decisions and backlog; current module status is in the delivery tracker.

# Historical milestone 0.1.0

## Baseline

The source is the completed **Audit GeoDrill Pro specification** chat (`01a0e1b2-a5a1-75d1-b746-57710dcc329b`), read on 27 September 2026. Its three final artifacts are preserved in `audit/part-1.md`, `part-2.md`, `part-3.md`. The original `Project Drilling Engineer.md` remains untouched in the parent directory.

The audit's final priority is a small complete read-only workflow before the research/control modules. This milestone implements that workflow with synthetic and user-imported historical data. It does not treat the review document as evidence of field qualification or domain-authority approval.

## Implemented model contracts

### Minimum curvature (M1 subset)

Inputs: MD in metres; inclination from downward vertical and azimuth clockwise from declared north in radians. Initial station is at MD=0 and N=E=TVD=0. Stations must strictly increase in MD. The dogleg is `acos(clamp(cos(I1)cos(I2)+sin(I1)sin(I2)cos(A2-A1),-1,1))`. Ratio factor is `2*tan(beta/2)/beta`, using `1+beta²/12+beta⁴/120` below 1e-4 rad. Apply the half-sum of the two station direction vectors times interval MD times ratio factor. Antipodal directions are rejected.

The implementation is verified against vertical/straight and independently derived circular-arc cases. It has no survey uncertainty model. Tool-dependent uncertainty is separate from interpolation, consistent with the [ISCWSA guidance](https://www.iscwsa.net/committees/error-model/). Original equations appear in audit Part 1, Section 5.1.

### MSE (M10 subset)

`MSE = W/A + T*omega/(A*v)`, `A = pi*d²/4`; SI result Pa. Numerical input envelope: W and T nonnegative and ≤1e8 in their respective SI units; omega ≤1000 rad/s; 0≤v≤10 m/s; 0.001≤d≤2 m. These broad numerical bounds are **not operating limits**. ROP ≤1e-5 m/s and any state other than confirmed drilling withhold the output. All imported telemetry uses the surface proxy label. The model does not diagnose drilling dysfunction. Source equations: audit Part 1, Section 5.10, referencing Teale's original specific-energy model.

### Pressure balance (M6 subset)

`Pbottom,gauge = Psurface,gauge + rho*g*TVD + supplied_annular_loss`, using g=9.80665 m/s². Equivalent density is Pbottom,gauge/(g*TVD), explicitly including surface backpressure. The entered pore and fracture pressures must share that gauge reference and the entered TVD. The comparison evaluates only that point. Constant density and steady single-phase conditions are required; annular friction is **not** predicted. No well-control advice is emitted.

## Architectural choices for this milestone

- React/TypeScript browser UI and local FastAPI implement the first slice. Tauri packaging is deferred; the machine has no available Rust compiler/cargo. This is a deliberate delivery boundary, not a claim that a desktop executable was produced.
- Plain authored CSS and SVG support the restricted charts and section/plan views. Tailwind, D3 and Three.js are not necessary for these views and have not been added speculatively. Full 3D visualization remains unimplemented.
- Polars writes normalized Parquet; DuckDB reads it with bounded workload. SQLite owns project metadata, events, calculations and fixed report snapshots.
- Synchronous calculations run on FastAPI's worker thread boundary; this release has no heavy solvers or separate job-worker service.
- Mutation operations serialize in one process. Do not run multiple API workers. Multi-process job orchestration remains a later architecture gate.
- The local API uses a random process session in an HttpOnly SameSite=Strict cookie, same-origin checks, a custom mutation header, exact host restrictions and loopback binding. This does not provide named-user identity or isolation from other trusted local processes.
- No cloud service, account, subscription, telemetry upload or equipment connection is needed.
- Ingest failures do not register partial datasets. A crash after writing a file but before committing metadata can leave an unreferenced file; garbage collection and full crash/fault-injection recovery are deferred.
- Report exports include canonical records and source hashes, not original source bytes. The originals remain in local storage. Copy the complete data directory for a full backup.

## Next backlog

| Order | Capability | Acceptance gate |
|---|---|---|
| 1 | Independent review of the implemented model/input specifications | Domain reviewers approve intended use, assumptions and reference cases; no operational qualification inferred from this coding milestone |
| 2 | Reviewable mapping preview, source provenance and project/run revisions | Source datum, pressure semantics, channel locations, sample cadence and bit/run changes are explicit; preview before commit |
| 3 | Tauri shell and signed Windows installer | Rust/build prerequisites, process supervision, authenticated sidecar startup, packaged runtimes, offline install and recovery tests |
| 4 | Whole-well geometry and restricted steady hydraulics | Hole/casing/BHA records and reviewed rheology/friction models; independent flow-loop/PWD evidence and allocated error budget |
| 5 | Large-file asynchronous LAS/CSV ingestion | Bounded RAM, progress/cancel, durable jobs, parser hardening and declared hardware/file workload |
| 6 | Arrival-time/as-known replay and live-source quality | Acquisition and receipt time preserved; out-of-order reconciliation; stale/disconnect states; one qualified read-only interface |
| 7 | Named roles, audited revisions and anchored evidence | Explicit local identity, record ownership, immutable revisions, signed export/update policy, documented recovery |
| 8 | M2 casing records, M1 3D and stratigraphy edits | Geometry invariants, explicit interpretation revisions, no unsupported integrity/isolation approval |
| 9 | Qualified analytics/ML | Each audit prerequisite, blind validation and applicability/abstention gate met per capability |

M17 remains excluded. Implementing these backlog items does not authorize equipment control.
