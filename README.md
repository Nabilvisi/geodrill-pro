# GeoDrill Pro Engineering Workstation

**Verified publication — 7 October 2026:** [PR #2](https://github.com/Nabilvisi/geodrill-pro/pull/2) is merged into `main` at `8dd27e73331e97305109518be200a0bf29b3a3c6`. [Streamlit](https://geodrill-pro.streamlit.app/) renders **0.9.0-alpha.1** with matching compiled asset hashes and a verified original survey/report workflow. [Windows research-6](https://github.com/Nabilvisi/geodrill-pro/releases/tag/research-6) is published as an explicitly unsigned prerelease. The downloaded executable passed survey import, saved geometry, calculation and canonical report checks. Local and Windows/Linux source CI each passed **683 tests**; the Windows release job also passed 683 tests and installer/backup/restore/uninstall checks. Full v0.9 architecture acceptance remains open. [Detailed verification](docs/evidence/v09-verification.json).

**Current source candidate: 0.9.0-alpha.2 — engineering research workstation preview.** The next bounded increment adds immutable wellbore-owned planned/actual/scenario survey and trajectory revisions, scoped engineering context, saved uncertainty/proximity, dependency staleness and hierarchy-aware report/recovery. The local suite passes **697 tests**. [Increment acceptance](docs/V09-WELLBORE-REVISIONS.md) and [template-based progress](GEODRILL_PRO_V0.9_PROGRESS.md) distinguish candidate verification from publication. The published app and research-6 remain alpha.1. Docking/themes, Three.js, Tauri/updater, enterprise infrastructure and independent qualification remain open.

The release paragraphs below are historical v0.8 milestones at their recorded revisions.

Published [research-5](https://github.com/Nabilvisi/geodrill-pro/releases/tag/research-5) verification: **635 tests passed locally, on Windows and Linux CI, and in the Windows release job**. Formation geomechanics now has a survey-bound input/import/calculation workflow, editable core/calibration evidence, stress plots and sampled elastic pressure intervals. Complete and withheld studies were saved and reopened on the hosted app; the actual downloaded portable executable also passed import, calculation, citation and fixed-report checks. Installation, backup/restore and uninstall passed; all four public downloads matched their hashes. [Geomechanics release evidence](docs/evidence/geomechanics-verification.json) identifies exact source, hosted assets and package hashes. Remaining software and qualification gaps are tracked in [the delivery matrix](docs/IMPROVEMENT-PLAN.md).


**Preserved v0.8 foundation — Engineering research workstation (GD-A01–A18).** The audited engineering workstation links source data → studies → scenario comparisons → programme governance → verified export and recovery.

See **[Current Improvement Plan](docs/IMPROVEMENT-PLAN.md)** for reconciled roadmap status, delivered increments, and pending gates. [VERIFICATION.md](docs/VERIFICATION.md) records dated, reproducible test evidence across the implemented modules, including the connected project journey and ISCWSA diagnostic benchmarks. [PROGRESS-AND-ROADMAP.md](docs/PROGRESS-AND-ROADMAP.md) provides the complete implementation sequence.

> [!NOTE]
> See docs/evidence/geomechanics-verification.json for current regression, hosted and artifact evidence; connected-increments-verification.json and repair-verification.json record earlier increments. The 6 October claim that all commercial gates were closed has been withdrawn. Unsigned Windows research packaging, trusted publisher signing, public deployment, independent petroleum engineering qualification and external security review are tracked separately. Release evidence binds each verified surface to its actual revision or asset hash. Equipment control and autonomous rig actuation remain strictly excluded (`equipment_control: false`).

[MODULES-1-17.md](docs/MODULES-1-17.md) maps delivered capabilities and boundaries. [MODEL-SPECS-0.8.md](docs/MODEL-SPECS-0.8.md) declares equations and applicability.

## Hosted Streamlit app

Open **[GeoDrill Pro on Streamlit](https://geodrill-pro.streamlit.app/)**. The refreshed preview groups named workspaces under Projects, Plan & Design, Engineering, Operations and Governance, using the existing Python API through an isolated browser-session workspace. Directional and the interim spatial viewer disclose actual source/revision context. The architecture's full five-pillar mapping remains an acceptance item. Start with North Sea · Research for telemetry/survey/log replay. Switch to Cloud verification · Synthetic for saved research workflows, including formation geomechanics and offset benchmarks. The in-app Start here guide explains imports, geometry revisions and fixed report downloads. On phones, the Open page selector provides named navigation. See the dated verification record for the deployed asset identity.

The hosted workspace is temporary. Download complete evidence reports before leaving; reports are not a restorable project backup. Use the local workstation when persistent project storage is required. All included examples are synthetic and equipment control remains unavailable.

The source repository is [Nabilvisi/geodrill-pro](https://github.com/Nabilvisi/geodrill-pro). See [CLOUD-DEPLOYMENT.md](docs/CLOUD-DEPLOYMENT.md) for runtime/deployment details and [VERIFICATION.md](docs/VERIFICATION.md) for test and live-release evidence.

## Open the app

On this computer, double-click **Start GeoDrill Pro.cmd**. It starts a hidden local service and opens `http://127.0.0.1:8765` in your default browser. If the service is already running, it opens the existing instance. **Stop GeoDrill Pro.cmd** stops only the responding installation and retains all data.

Chrome and the built-in Codex browser were both used to exercise the app. An initial navigation rejection was corrected in the application's local request boundary; Chrome now opens the workstation. No browser protection or extension setting was changed. At the original milestone, the connected Chrome file chooser was unavailable and the upload check used the built-in browser. Version 0.4.0 additionally verifies the EM JSON upload through an isolated Chrome profile using agent-browser.

The installed environment and built assets are already in this project directory. Starting the app requires no network connection. Dependency installation on a new computer requires network access unless packages have been provisioned separately.

## Connected offset and evidence workflows

Offset benchmarks preserve typed SI input JSON, source hashes, immutable geometry context, filtering/exclusion reasons and empirical duration/cost quantiles. Mixed currencies are excluded; unknown evidence or fewer than three eligible records withholds projections. Rig-time cost at the entered daily rate is a separate scenario. Supplied adjudication notes do not establish independent DDR verification.

Evidence search lists project-scoped citations with the correct hash basis, all programme version references and historical casing differences. Inspect cited record opens the stored dataset, geometry, calculation or programme. A missing match or varying historical geometry withholds a single answer. This is metadata search; it does not infer engineering answers from full document text.

## Formation geomechanics

The Formation geomechanics page derives MD/TVD/inclination/azimuth from the accepted survey, preserves original JSON and immutable geometry, and exposes supplied core and closure-pressure records. It evaluates isotropic elastic wall-principal stresses with Mohr–Coulomb or Mogi–Coulomb criteria and a restricted linear hydrostatic density scenario. Missing or conflicting evidence withholds results; refinement failures suppress pressure intervals. The intervals are sampled research scenarios, without mud-window approval or equipment authority. [Implementation and remaining original GD-A17 scope](docs/GD-A17-IMPLEMENTATION.md).

## What works

- Create projects with explicit well, depth datum, north reference and bit diameter.
- Import telemetry CSV with explicit units; convert at the boundary to SI.
- Preserve missing and negative observations with ineligible calculations withheld.
- Retain original file bytes and SHA-256, normalized Parquet, source-row provenance, and mapping metadata.
- Import directional surveys and calculate minimum-curvature north/east/TVD coordinates.
- Edit interpreted tops, uncertainty bands, hole sections and casing records; preserve geometry revisions.
- Inspect 3D, section and plan views, with equal spatial scale and every horizontal-top intersection.
- Screen supplied casing load cases against body/connection evidence and Lamé/von Mises yield; compare preserved scenarios.
- Cluster native-depth LAS responses with declared feature units/envelopes, training-only scaling, seeded initializations and missing-data gates. These are exploratory response groups.
- Compare M4 laminated/dispersed/structural wet-shale volume scenarios, coexisting-texture alternatives and endpoint sensitivity. Total and primary porosity are displayed separately; raw/unknown correction states withhold interpretations.
- Preserve M5 vendor-result JSON with tool/model metadata, supplied uncertainty, acquisition/receipt timestamps, native MD and quality flags. Review it against a saved geometry revision; unsupported samples remain withheld.
- Import a restricted LAS 2.0 subset: unwrapped, unique curves, explicit depth units, declared NULL sentinel, monotonic index.
- Plot telemetry and replay source time with play/pause, seek and speed controls. Gaps greater than 5 seconds are reported and not joined across in plots.
- Calculate Teale MSE or a labeled surface proxy; abstain at low ROP or outside the declared drilling state.
- Calculate M6 steady laminar pipe/annulus losses with Newtonian/Bingham/Herschel–Bulkley rheology; preserve mud-test age, string geometry, nozzle and rating evidence, continuous pressure margins and tested parameter corners.
- Calculate M7 geometry-oriented effective Kirsch wall stresses, restrained-wall thermal estimates and supplied-strength screens; preserve externally supplied pressure bounds without verifying approval.
- Track M8 dilute vertical Stokes settling and generated/returned/retained solids with a conserved tank balance and hydraulic-source reference.
- Run M9 offline motion-history acoustic piston surge/swab in a uniform annulus with pressure margins, conserved compressible storage and three-grid refinement.
- Calculate M10 quasi-static soft-string pickup/slackoff/rotating/combined load profiles, friction sensitivity, supplied rating margins and observed residuals.
- Screen M11 local effective compression against reduced sinusoidal/helical thresholds; retain uncertainty and conditional helical axial-force transfer tied to M10.
- Simulate M12 coupled axial/torsional/lateral generalized coordinates for a straight uniform cantilever; review original native acceleration records separately.
- Preserve M13 recovered-bit inspections, evidence availability and censored cohort histories; show conditional costs without an individual-life or trip recommendation.
- Track M14 material-specific casing wear, separate fatigue exposure, inspection residuals and a restricted uniform-wall pressure/yield scenario.
- Replay M15 native flow/stock balances with causal persistence, explicit unknown intervals and supplied-event evaluation.
- Review M16 external mud/gas phase evidence and closed-batch replay; evaluate an additional characterized nonpolar binary equilibrium research case.
- Run M17 bounded pressure-plant/PID simulations with request authorization, lease/expiry/idempotency/rate/slew checks and fault/manual-override cases.
- Import/export complete strict SI study JSON for M12–M17, retaining original bytes, SHA-256 and canonical Parquet documents.
- Reopen exact saved module inputs/results; changed assumptions create new immutable studies.
- Retain the original single-depth constant-density balance in Engineering lab, with supplied annular loss and explicit gauge reference.
- Review data events and save an acknowledgement note without resolving or suppressing the original condition.
- Create, reopen and download fixed JSON evidence snapshots, or print a report summary.
- Verify a local hash-linked audit chain and file integrity.
- Inspect the status of all 17 modules in the capability roadmap.

The base demonstration contains 240 generated telemetry rows, eight survey stations and five LAS rows, including missing SPP, connection intervals, low ROP and a 26-second source-time gap. It is not Volve, FORGE or field data. M4 adds a separate synthetic ten-sample PHIT/VSH source. M5 adds a separate eight-sample vendor-interchange example with no physical EM instrument or forward solve. M6 adds explicitly generated fluid, string, nozzle, rating and pressure-window assumptions against a saved geometry revision; these are not field measurements.

## Modules 12–17 demonstration

Select **Modules 12–17 · Software verification**. This explicitly synthetic project has a straight survey and a planned casing record, plus saved successful and withheld cases. Open one of the six new pages and click a study in Saved studies to reopen its exact input/output. The final BHA and casing records begin with **Verified synthetic**; the supervisory fault case is **Synthetic supervisory faults and fresh recovery**.

Use **Export SI inputs** to retain a complete study document and **Study input JSON** to import one. Pressure and force fields display engineering units; the JSON contract uses SI. Records beyond the first 24 remain retained, and result-table previews retain the full underlying evidence in saved reports. Editing imported inputs creates a new immutable calculation with an explicit original-document match state.

Saved cases demonstrate unsupported BHA boundaries, future bit inspection evidence, unobserved casing exposure, missing flow samples, unsupported native actual-mud prediction, and absence of simulation authority. These retain explicit withholding/rejection reasons. The gas page also has a synthetic external-phase replay; supplied review/convergence flags do not constitute independent qualification.

The **North Sea · Research** project retains the original M1–M11 data and adds six geometry-bound studies through M17. Its fixed integrated report includes all implemented modules; an unsupported structural interval may correctly be withheld. Open Reports to inspect or download a complete fixed snapshot. Both the integrated report and dedicated six-module verification report are preserved under docs/evidence.

## Modules 7–10 demonstration

The app navigation contains Wellbore stability, Cuttings transport, Surge & swab and Torque & drag. The saved project **Modules 7–10 · Vertical verification** uses a labelled generated vertical survey and uniform hole. North Sea · Research retains the prior modules and demonstrates the deviated-transport withholding gate.

Open a module, inspect its draft assumptions, calculate and save, then reopen a study from Saved studies. For M8/M9, select a saved M6 result with the same geometry; synthetic projects can explicitly create a Newtonian source through the provided button. Reports preserve every study and its linked source, including withheld results. Use Engineering lab for the existing MSE workflow.

See [MODEL-SPECS-0.6.md](docs/MODEL-SPECS-0.6.md) for equations, input references, numerical checks and model limits.

## Release limits

M4 requires compatible total physical porosity and wet-shale volume assumptions. Its mathematical topology scenarios do not confirm geology, connected pores, permeability or net pay. Sensitivity uses tested parameter corners, not calibrated confidence intervals. Apparent sonic/neutron porosity is not silently converted; specialist calibration and independent validation remain open.

- **Research and historical review only.** No operational recommendations, approvals, alarm protection, automatic well-control actions, or equipment write routes.
- **Per import: 2 MiB; up to 10,000 generic data rows or 1,000 EM interchange samples.** This release is not qualified for multi-gigabyte ingestion or continuous live monitoring.
- M6 calculates a geometry-linked **steady laminar profile** in a declared constant-density, concentric, stationary-wall envelope. Transition/turbulence, eccentricity, rotation, cuttings loading, thermal/compressible/multiphase and transient flow remain unsupported. See [MODEL-SPECS-0.5.md](docs/MODEL-SPECS-0.5.md). The older Engineering lab balance still uses supplied single-point loss. No mud/pump advice, operating approval or API RP 13D compliance is claimed.
- M7 uses isotropic elasticity and a uniform restrained-wall thermal estimate; coupled pore/thermal diffusion, plasticity and anisotropic rock are unavailable. It generates no operational stability bounds.
- M8 supports near-vertical dilute spherical-particle Newtonian transport; non-Newtonian settling, rotating/eccentric flow and deviated cuttings beds remain unqualified.
- M9 is a reduced fixed-annulus acoustic displacement model. It excludes full moving-wall entrainment, internal-flow transients, gel, gas and diameter transitions; pressure extrema and refinement are numerical indicators.
- M10 torque/drag omits stiffness, buckling, inertia and pressure end forces. Friction ranges and observed residuals are not calibrated field predictions.
- M12 models three reduced generalized coordinates of a straight uniform segment. Curved/full-contact BHA dynamics, fitted sensor observability and virtual downhole diagnostics are unavailable.
- M13 cohorts and costs are descriptive and conditional. Independent censoring is assumed; no individual remaining-life or operational recommendation is issued.
- M14 requires supplied material/exposure evidence. Localized grooves and incomplete exposure withhold the residual capacity screen; connection/barrier approval is absent.
- M15 is an offline causal balance replay. Manufactured event metrics do not establish calibrated kick/loss detection or protective alarm performance.
- M16 native binary EOS is not actual-mud solubility. External phase flags remain supplied evidence; batch replay does not solve coupled wellbore momentum, energy or slip transport.
- M17 has a simulated plant and validator only. It has no rig network adapter, hardware-command endpoint or authority to control equipment (`equipment_control: false`).
- MSE uses surface observations for imports. Downhole energy losses, motor power and synchronization error are not inferred.
- Replay supports **source-time playback**. ETP/WITSML streaming and arrival-time reconstruction remain unimplemented; see [GD-A07 status](docs/GD-A07-IMPLEMENTATION.md).
- Directional surveying includes WGS84 UTM projections, ISCWSA MWD Rev5.11 positional uncertainty propagation benchmarked against diagnostic cases, tie-in covariance, multi-tool intervals, and 3D closest approach (GD-A10, `clearance_generated: false`).
- Added research calculations include laminar Herschel-Bulkley hydraulics and no-slip cuttings mixture density, a reduced bending-gradient torque/drag extension with supplied calibration/holdout points, casing-collapse/load-envelope screens, IADC inspection progression and offline causal anomaly replay. Dynamic deviated cuttings beds and clearance-dependent stiff-string contact remain unsupported. Offset percentile and Mogi-Coulomb kernels have tests but are not connected app workflows. Evidence search is available through the API. [The delivery matrix](docs/IMPROVEMENT-PLAN.md) records remaining integration and qualification requirements.
- Multi-user governance supports named roles (Engineer/Author, Reviewer, Approver, Admin), four-eyes review controls, and Ed25519 digital server attestations (GD-A09).
- Project backup and disaster recovery supports scoped `.gdpz` archives and verified fresh-directory restoration with preserved cryptographic hashes and signatures (GD-A08).
- Standalone Windows packaging provides portable `dist/GeoDrillPro-Windows-x64.zip` containing `GeoDrillPro.exe` (PyInstaller 6.22.3). Installer code-signing and external third-party security audits remain separate pending gates.

## Data location and recovery

By default, data is under `data/`: SQLite state, original sources in `raw/`, normalized files in `parquet/`, and service logs. In standalone executable mode, user data is isolated in `%APPDATA%/GeoDrillPro/data`. The service listens only on `127.0.0.1`. It has no outbound data upload functionality.

**This checkout is in OneDrive. The operating system's OneDrive client may synchronize its contents independently of GeoDrill.** For real project data, use an approved non-synchronized directory by setting `GEODRILL_DATA_DIR` before starting the app. Stop the application before switching the data directory. Existing data is not automatically moved.

For project exchange, the API provides `.gdpz` archives through `services/api/storage.py`. Current source also provides whole-workstation SQLite/file recovery through `tools/backup_restore.py` and desktop recovery arguments. These commands require a packaged release newer than research-2. See [recovery instructions](docs/GD-A08-IMPLEMENTATION.md) for preserved evidence, sensitive backup contents and fresh-directory restore. Trusted publisher signing, automatic update/binary rollback and broader crash/disk-full qualification remain open.

## Import contracts

Telemetry requires exactly these channel names, with **one** supported unit for each, plus `timestamp` and `state`:

| Channel | Supported header units | Canonical storage |
|---|---|---|
| `md`, `tvd` | `m`, `ft` | m |
| `wob` | `N`, `kN`, `klbf` | N |
| `torque` | `N.m`, `kN.m`, `ft.lbf` | N·m |
| `rpm` | `rpm`, `rad/s` | rad/s |
| `rop` | `m/h`, `m/s`, `ft/h` | m/s |
| `spp` | `Pa`, `MPa`, `psi` | Pa |
| `flow` | `m3/s`, `L/min`, `gpm` | m³/s |

Example: `wob[kN]`, **not** `WOB`, `wob` or a guessed unit. Timestamps must be ISO 8601 with timezone and strictly increasing. Accepted states are `drilling`, `connection`, `off_bottom`, `unknown`. Blank numeric cells remain null. NaN, infinity, duplicate times, unknown units, extra columns and inconsistent row widths are rejected. The source dictionary must identify the meaning of measured pressure before any use beyond historical display; the telemetry adapter does not assume it is an absolute pressure.

Survey headers: `md[m],inclination[deg],azimuth[deg]`. `md[ft]` and matching `inclination[rad],azimuth[rad]` are supported. First MD must be zero; MD strictly increases; inclination is 0–180°; azimuth is 0–less than 360°. Antipodal station directions are rejected.

Download synthetic examples from the Data workspace. Imported data belongs to the active project's fixed datum and bit context; create a separate project for a different run or bit. Review references before importing. This initial release does not verify the user's declared datum against external survey metadata.

## Rebuild on a new Windows workstation

Prerequisites: Python 3.12, a supported Node.js installation and pnpm. The current machine uses Codex's bundled runtimes. No Rust toolchain was present or installed for this milestone.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
pnpm install --frozen-lockfile
.\.venv\Scripts\python.exe tools\build.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools\launch.py
```

After moving an installed checkout, use tools/build.py to rebuild from the installed Node tools. The helper compiles into a fresh dist/release directory and selects it only after success; restart the service to activate it. This avoids overwriting Windows-locked frontend files. The pnpm build script delegates to the same helper. Project pnpm-workspace.yaml disables pnpm's automatic pre-script reinstall, which otherwise attempts to purge the relocated modules directory; explicit dependency installation remains a separate setup step. pnpm may retain obsolete absolute store paths and try to reinstall; the helper avoids that relocation problem. No new runtime dependencies were added for Modules 7–17.

Direct Python dependencies are in `requirements.txt`; the complete verified environment is in `requirements-lock.txt`. `pnpm-lock.yaml` pins the frontend graph. For source development, run the API and `pnpm dev` separately; the shipped launcher serves only the compiled frontend, not the Vite development server. One API worker is required for the process-local session and mutation lock.

## Repository

| Path | Responsibility |
|---|---|
| `apps/desktop/src` | React/TypeScript interface and SVG data views |
| `services/api` | Local FastAPI boundary, SQLite/Parquet storage, synthetic fixtures |
| `packages/engineering` | Typed contracts, unit-aware import adapters, deterministic kernels |
| `tests` | Numerical, property, contract, persistence and request-boundary checks |
| `tools` | Local lifecycle, lockfile and evidence utilities |
| `public` | Packaged local assets |
| `docs/audit` | All three final responses from the prior audit, preserved verbatim |
| `docs` | Model limits, implementation decisions, verification and next backlog |

No pretrained facies model, external credential, rig address, Modbus client or control command adapter is present.

## Scope and qualification

See `docs/IMPLEMENTATION.md` for the implemented subset, deviations and prioritized follow-on work. See `docs/VERIFICATION.md` for actual test evidence and remaining validation gaps. Passing software tests does not establish physical model accuracy or operational readiness.
