# GeoDrill Pro Engineering Workstation

**Version 0.8.0 — Completed Engineering Workstation (GD-A01–A18).** The audited engineering workstation links source data → studies → scenario comparisons → programme governance → verified export and recovery.

See **[Current Improvement Plan](docs/IMPROVEMENT-PLAN.md)** for reconciled roadmap status, delivered increments, and pending gates. [VERIFICATION.md](docs/VERIFICATION.md) records verified test evidence across all modules (537/537 tests pass, 100%), including the connected project journey and ISCWSA diagnostic benchmarks. [PROGRESS-AND-ROADMAP.md](docs/PROGRESS-AND-ROADMAP.md) provides the complete implementation sequence.

> [!NOTE]
> Software completion in this checkout is verified by automated test suites (537 passing tests). Standalone Windows packaging, shared production deployment, and independent petroleum engineering or security qualification remain separate, pending gates. Do not assume this checkout, the Windows executable, and the hosted Streamlit deployment contain identical releases without explicit verification. Equipment control and autonomous rig actuation remain strictly excluded (`equipment_control: false`).

[MODULES-1-17.md](docs/MODULES-1-17.md) maps delivered capabilities and boundaries. [MODEL-SPECS-0.8.md](docs/MODEL-SPECS-0.8.md) declares equations and applicability.

## Hosted Streamlit app

Open **[GeoDrill Pro on Streamlit](https://geodrill-pro.streamlit.app/)**. The hosted app retains all 17 workstation pages and uses the existing deterministic Python API through an isolated browser-session workspace. Start with North Sea · Research for telemetry/survey/log replay. Switch to Cloud verification · Synthetic for saved M12–M17 studies. The in-app Start here guide explains imports, geometry revisions and fixed report downloads. On phones, the Open page selector provides named navigation to all 24 workspace pages.

The hosted workspace is temporary. Download complete evidence reports before leaving; reports are not a restorable project backup. Use the local workstation when persistent project storage is required. All included examples are synthetic and equipment control remains unavailable.

The source repository is [Nabilvisi/geodrill-pro](https://github.com/Nabilvisi/geodrill-pro). See [CLOUD-DEPLOYMENT.md](docs/CLOUD-DEPLOYMENT.md) for runtime/deployment details and [VERIFICATION.md](docs/VERIFICATION.md) for test and live-release evidence.

## Open the app

On this computer, double-click **Start GeoDrill Pro.cmd**. It starts a hidden local service and opens `http://127.0.0.1:8765` in your default browser. If the service is already running, it opens the existing instance. **Stop GeoDrill Pro.cmd** stops only the responding installation and retains all data.

Chrome and the built-in Codex browser were both used to exercise the app. An initial navigation rejection was corrected in the application's local request boundary; Chrome now opens the workstation. No browser protection or extension setting was changed. At the original milestone, the connected Chrome file chooser was unavailable and the upload check used the built-in browser. Version 0.4.0 additionally verifies the EM JSON upload through an isolated Chrome profile using agent-browser.

The installed environment and built assets are already in this project directory. Starting the app requires no network connection. Dependency installation on a new computer requires network access unless packages have been provisioned separately.

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
- Replay supports **source-time playback** and **ETP 1.2 / WITSML 2.1 read-only streaming ingestion** with arrival-time vs source-time gap inspection (GD-A07).
- Directional surveying includes WGS84 UTM projections, ISCWSA MWD Rev5.11 positional uncertainty propagation benchmarked against diagnostic cases, tie-in covariance, multi-tool intervals, and 3D closest approach (GD-A10, `clearance_generated: false`).
- Advanced engineering includes non-Newtonian Herschel-Bulkley hydraulics with dynamic cuttings bed transport (GD-A11), 3D stiff-string torque & drag with calibrated friction and vibration screening (GD-A12), API TR 5C3 / ISO 10400 casing collapse and operational load lines (GD-A13), offset well P10/P50/P90 benchmarking (GD-A14), 8-position IADC dull grading bit wear mechanics (GD-A15), passive anomaly advisory with disjoint validation (GD-A16), 3D in-situ stresses and Mogi-Coulomb geomechanics (GD-A17), and permission-aware evidence search with SHA-256 citations (GD-A18).
- Multi-user governance supports named roles (Engineer/Author, Reviewer, Approver, Admin), four-eyes review controls, and Ed25519 digital server attestations (GD-A09).
- Project backup and disaster recovery supports scoped `.gdpz` archives and verified fresh-directory restoration with preserved cryptographic hashes and signatures (GD-A08).
- Standalone Windows packaging provides portable `dist/GeoDrillPro-Windows-x64.zip` containing `GeoDrillPro.exe` (PyInstaller 6.22.3). Installer code-signing and external third-party security audits remain separate pending gates.

## Data location and recovery

By default, data is under `data/`: SQLite state, original sources in `raw/`, normalized files in `parquet/`, and service logs. In standalone executable mode, user data is isolated in `%APPDATA%/GeoDrillPro/data`. The service listens only on `127.0.0.1`. It has no outbound data upload functionality.

**This checkout is in OneDrive. The operating system's OneDrive client may synchronize its contents independently of GeoDrill.** For real project data, use an approved non-synchronized directory by setting `GEODRILL_DATA_DIR` before starting the app. Stop the application before switching the data directory. Existing data is not automatically moved.

For backup, GeoDrill Pro provides complete `.gdpz` project archives (`tools/backup_restore.py`, `packages/engineering/scenarios.py`) and consistent SQLite backup. Restoring into a fresh directory re-verifies all source hashes, calculation identities, and digital attestations before reopening. Signed/encrypted installers and crash/disk-full recovery qualification remain future work.

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
