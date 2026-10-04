# Verification record — 4 October 2026 / version 0.8.0

## Streamlit cloud release verification — 2026-10-05

The source was published to Nabilvisi/geodrill-pro. GitHub currently reports the repository as public; visibility was verified directly from its metadata on 2026-10-05. The user deployed https://geodrill-pro.streamlit.app/. The cloud interface retains the existing 17-module workstation and deterministic backend, with separate temporary browser-session workspaces.

- Full regression suite: 422 passed in 52.66 seconds against the pinned cloud requirements (Python 3.12, Streamlit 1.65.0, PyArrow 24.0.0).
- After the onboarding change, the 16 cloud checks passed again in 11.86 seconds. One existing Starlette/httpx deprecation warning remains.
- Production TypeScript/Vite build and Streamlit component packaging succeeded.
- Actual local Streamlit UI checks covered a new study save, reopening the same calculation identity/results, and exact exported SI input bytes submitted through the rendered File/change handler. This is not a file-chooser automation claim.
- Original API report bytes are prepared as a native download link. Re-serializing parsed report numbers in JavaScript was rejected after its downloaded snapshot failed the canonical fingerprint check.
- The corrected complete browser download passed an independent canonical SHA-256 check; evidence is in evidence/streamlit-browser-report-verification.json.
- Local layout at an outer width of 390 px had outer scroll width 390 px and inner width/scroll width 358 px. The browser application-error list was empty.

The public app returned a healthy 200/ok response and served JavaScript/CSS identical to the tested build. A new live supervisory calculation was saved, and a 58-byte synthetic survey was imported through the rendered File/change handler. The actual 2,253,207-byte browser report download contains seven calculations across six research models and matches canonical SHA-256 81db38959080c3c347625ab07a9f68d78d3cf7a28cc4eeca0828ed42935c8cd3. The imported source hash matches the exact supplied bytes. Live workflow evidence is in evidence/streamlit-live-verification.json; asset checks are in evidence/streamlit-live-assets.json. The final mobile selector was also exercised on the public deployment: it provides 24 named pages and opens a roadmap with all 17 module cards without horizontal overflow. The final compiled JavaScript and CSS hashes both match the deployed bytes, and live health is 200/ok. Temporary cloud workspaces and fixed reports are not a persistent account database or a restorable project backup.


## Completed audited research software through Module 17

**406 automated tests pass**, including 102 new numerical, contract, eligibility, authorization and persistence cases for Modules 12–17. The 304 prior cases remain passing. One existing Starlette/httpx TestClient deprecation warning remains. TypeScript compilation and the final production Vite build pass; a final visual correction labels gas molar volume as m³/mol without changing its stored SI value.

The delivered target is the audited MVP/research scope in [MODULES-1-17.md](MODULES-1-17.md). [MODEL-SPECS-0.8.md](MODEL-SPECS-0.8.md) records numerical assumptions and exclusions. Successful manufactured examples and software checks do not supply field model qualification.

### Numerical and contract evidence

- M12: independent uncoupled modal frequencies, coupled eigen-residual/orthogonality, a zero-initial-condition sinusoidal response and RK4 error reduction; contact energy/work/dissipation, complete-history refinement and survey/clearance/native-sampling gates.
- M13: failure/censor ties and risk sets, descriptive survival and cost arithmetic, future evidence exclusion, recovered inspection contracts and supported age/horizon limits. Individual remaining life and trip authorization are absent.
- M14: dimensional wear/contact arithmetic, coefficient corners, independent closed-end Lamé/von Mises expression, log–log S–N/Miner arithmetic, inspection residuals and unsupported mechanism/exposure gates.
- M15: exact manufactured control-volume balance, causal prefix invariance, unknown sample/state/gap persistence resets, complete missed/unmatched event evaluation and native record retention.
- M16: cubic roots, Rachford–Rice, fugacity/material-balance equality and nontrivial binary split, single-phase/unsupported-fluid gates, external evidence/composition/geometry checks and independent exponential batch relaxation/refinement.
- M17: exact first-order plant limit, default-deny request checks, exact configuration digest, TTL/lease/duplicate/rate/slew constraints, bounded PID/antiwindup, queued-request invalidation during faults, manual override, unknown/disconnected readiness and process-envelope reporting.
- API: original UTF-8 SI input bytes/hash plus canonical Parquet documents, strict ownership/model/datum/geometry and integrity checks, duplicate import handling, immutable calculations/report snapshots and persistence after reopening.

### Actual Chrome workflows

The project **Modules 12–17 · Software verification** uses explicitly manufactured geometry, records and signals. All six input JSON files were imported through Chrome's file input, calculated/saved, and reopened. The exact six final study identities were rechecked in the final compiled release after the actual service restart; structured evidence is [m1217-chrome-reopening.json](evidence/m1217-chrome-reopening.json).

1. M12 final coupled BHA study retains 101 native synthetic acceleration samples, a separate supplied-channel review and full response/refinement. Full-contact boundary selection produces a saved withheld study.
2. M13 four manufactured inspected/censored runs produce two confirmed failures and a stepped descriptive cohort curve. Future inspection evidence at the selected cutoff produces a saved withheld case.
3. M14 final uniform-wall scenario retains exposure, wear and separate fatigue, with planned casing explicitly identified. Declared unobserved exposure withholds residual strength.
4. M15 the original replay retains a balance candidate and supplied-event comparison. A null inlet sample remains unknown, produces two unknown intervals, interrupts persistence and visibly breaks native/balance plot segments.
5. M16 characterized binary equilibrium has vapor fraction 0.5474635114, fugacity log residual 8.5664061e-9 and material-balance residual 1.1102230e-16. The synthetic external-phase replay preserves inventory and supplied convergence/stability flags; native actual-mud prediction is withheld.
6. M17 baseline, faults/manual override and no-authority cases are saved. The fault simulation retains 241 accepted and 140 rejected requests; the no-authority case has zero accepted requests. Equipment control and network-adapter availability remain false.
7. The report dialog reopened a fixed snapshot. **Download complete JSON** produced an actual 6,162,356-byte Chrome download; parsed contents exactly match the saved report and its independently rehashed canonical snapshot. No browser protection setting was changed.
8. At 1440 × 1000, each final result fit the viewport. At 390 × 844, the saved M17 result has document width 390 px and no horizontal overflow; the result was visually inspected. Chrome's captured application-error list is empty.

Desktop evidence: [BHA](evidence/module12-dynamics.png), [bit cohort](evidence/module13-bit-runs.png), [wear/fatigue](evidence/module14-wear-fatigue.png), [flow replay](evidence/module15-flow-replay.png), [binary phase](evidence/module16-binary-equilibrium.png), [supervisory result](evidence/module17-final-result.png). Additional evidence includes withheld cases, external-phase replay, [mobile result](evidence/module17-mobile.png) and report dialogs.

### Final service, build and persistence

Final served release: dist/release-9f8bb45481c74142a36dc2c5ccf66bc9.

- index-Bc7C4wL3.js: SHA-256 3175fc09dcca124dd8aecb97e3c58e20982db8cfeba89c44fe4681e4d2261d6f (380826 bytes).
- index-CH3NGfKJ.css: SHA-256 ccff790a81d7ed9e8924bfe389510289134879ff65779c6e766b6010c8ba190a (38187 bytes).

The final identity-checked launcher restart changed service PID from 36056 to 40440. The six final calculations and five saved report snapshots were unchanged. Live HTML, JavaScript and CSS bytes match the selected completed build. Health reports version 0.8.0, mode local-research and equipment_control=false. The session has equipment_authority=none. Registered API declarations contain no hardware-command route; attempted command/equipment-write URLs return 404. The 110-entry local hash-linked audit chain verifies.

Installation: C:\Users\HP\OneDrive\Project Drill\geodrill-pro. This is the preserved existing installation, distinct from the obsolete Project Apps location. No previous project or report was replaced.

### Fixed report integrity

- a05ef9f0-9e3b-4f8d-bc74-05422cb9ad3a: SHA-256 781075331097c0fbd136593014cb4a000c35648fb5b174e52054dc5782eddedb; version 0.8.0.
- 597ebab6-0dd3-466a-8420-698129eb30ce: SHA-256 4d16ac076b8531da598b51203ca062523f66ab38289e27e4bcd98bfac354238b; version 0.7.0; preserved historical snapshot.
- 192073e1-671d-4587-a270-3046cda29c66: SHA-256 4bef5c4be0213e1acb16d809f010533f4d8ce5f03b1da7501d6be6662e8f8ae0; version 0.7.0; preserved historical snapshot.
- 7a89c96a-ce8d-486c-8424-57e0e6779d1d: SHA-256 d612f6c6fbe8bbb485ff1823e8882348c6e7734bace86eff9a2cf77feaecc21a; version 0.6.0; preserved historical snapshot.
- c9516f97-7440-4e39-8479-fe6340aeaf6d: SHA-256 ef84b610b8e6480a8230e7143d1ef143202ace529119de72cc58ab6aee2b9673; version 0.8.0.

The new North Sea integrated snapshot includes M1 engineering revisions and calculation models through M17; all original M1–M11 work is preserved. New integrated studies were calculated through the API against its existing immutable geometry. The dedicated six-module project supplies the Chrome form/import/save verification; unsupported intervals in the original curved geometry retain their explicit gates.

Evidence artifacts: [live release checks](evidence/m1217-live-verification.json), [Chrome saved-study checks](evidence/m1217-chrome-reopening.json), [actual Chrome report download](evidence/m1217-report-browser-download.json), [integrated Modules 1–17 report](evidence/modules1-17-report.json). The repeatable live helper is tools/verify_module17_release.py; it prepares an idempotent baseline and compares exact evidence when run with --after-restart.

### Remaining qualification boundaries

The audited software delivery is complete. No instrumented field BHA, independently calibrated bit-life cohort, material/fluid wear programme, adjudicated field anomaly corpus, actual-mud PVT/flow-loop programme or OEM hardware/HIL approval was supplied. Multiuser signatures, live WITSML, signed native installation and rig control remain outside this offline release. The application issues no operational clearance and has no equipment-write interface.

---

# Verification record — 4 October 2026 / version 0.7.0

## Completed Module 11 offline research workflow

- **304 automated tests pass**, including 47 new M11 cases. The full previous regression coverage remains passing. TypeScript compilation and the production pnpm run build command pass. One existing Starlette/httpx TestClient deprecation warning remains.
- Selected published-formulation coefficients are checked using explicitly manufactured SI inputs; an independent Rayleigh energy minimum recovers the sinusoidal long-pipe limit. Horizontal constant-helix axial force integration matches an independent Riccati solution. These are numerical equation checks, not laboratory or field validation.
- Tests cover effective-pressure-force signs, distinct sinusoidal/helical branches, modulus/clearance/load uncertainty, installed/planned casing clearance, all intersected survey arcs, short/vertical/upgoing intervals, material strain/slope guards, unsupported boundaries/rotation/tool joints, full-profile refinement and branch divergence.
- API tests check source ownership, same immutable geometry/datum, full saved-source hash, immutable report inclusion and reopening after a server restart. Reused load-depth indices avoid rebuilding the entire source profile for every interpolation.
- The release serves dist/release-495859c65ff940538a47875ea5aabf5f. Live JavaScript and CSS bytes match the selected local release:
  - index-CSf-ITLd.js: c08d1aee6b14bd0955e16f252eec39a49ac24eadec4688d6a060f26282421f91.
  - index-C1ziBOSM.css: 1fb118951baf73f16985f48307b2aedd7b1796e5482018a15b13dd487f0aee2b.

Chrome verification:

1. Saved a synthetic compressive slackoff M10 source through the form, then selected it in M11. The horizontal source is explicitly manufactured; no measured force is implied.
2. Saved and reopened Synthetic horizontal buckling and helical drag. For MD 0–400 m, sinusoidal estimate 115.477492 kN, helical estimate 163.309835 kN, and maximum baseline compression 195.738684 kN. The screen retained 241 profile points.
3. Conditional prescribed-bottom-force transfer converged at 512 cells; upper effective tension -259.635631 kN versus unbuckled -195.738684 kN. The difference is -63.896947 kN. Nominal and all 16 uncertainty-corner profiles were checked; worst refined difference 1.880107e-8 N.
4. The vertical verification project saved an inclination-gated withheld study. Pinned end conditions saved a separate withheld study. A 32-cell initial grid with a 1e-9 N tolerance saved an incomplete assessment, retaining the numerical reason and original screen.
5. Reopened the original saved inputs after the final service restart. The report dialog showed source inventory, calculations, geometry revisions and JSON export. Saved statuses, not descriptive study names, are authoritative.
6. Checked the result at 390 × 844 and 1440 × 1000. Mobile document width equals viewport width; the long wall-load editor button was corrected after visual inspection. No framework error overlay or application browser errors were observed.

Reports and live integrity:

- M11 horizontal verification report: 192073e1-671d-4587-a270-3046cda29c66; SHA-256 4bef5c4be0213e1acb16d809f010533f4d8ce5f03b1da7501d6be6662e8f8ae0.
- New North Sea report includes all implemented M1–M11 research workflows, including the original curved/rotating source's explicitly withheld M11 result: 597ebab6-0dd3-466a-8420-698129eb30ce; SHA-256 4d16ac076b8531da598b51203ca062523f66ab38289e27e4bcd98bfac354238b.
- Prior 0.6.0 report 7a89c96a-ce8d-486c-8424-57e0e6779d1d retains SHA-256 d612f6c6fbe8bbb485ff1823e8882348c6e7734bace86eff9a2cf77feaecc21a.
- All three report snapshots were independently rehashed from canonical JSON after restart. Audit chain integrity is verified; health reports version 0.7.0 and equipment_control false.

Evidence: [complete live checks](evidence/m11-live-verification.json), [M11 report](evidence/m11-report.json), [Modules 1–11 report](evidence/modules1-11-report.json), [desktop result](evidence/m11-final-result.png), [mobile result](evidence/m11-mobile-result.png), [boundary withholding](evidence/m11-boundary-withheld.png), [incomplete tolerance](evidence/m11-incomplete.png). Scope and requirement coverage are in MODULES-1-11.md and MODEL-SPECS-0.7.md.

---

# Verification record — 4 October 2026 / version 0.6.0

## Completed research build through Module 10

- **257 automated tests pass**: the prior 200 cases, 50 added M7–M10 numerical/API cases and seven completed-frontend-release selection cases. TypeScript compilation and production Vite build pass, including the standard pnpm run build command. The supported workspace verifyDepsBeforeRun setting avoids an automatic reinstall of relocated modules. One existing Starlette/httpx TestClient deprecation warning remains.
- M7 independent checks recover the Kirsch wall extrema, restrained thermal sign/magnitude, isotropic orientation invariance and principal-stress invariants. Invalid/unsupported tensor, thermal, strength and coupled-model cases are explicit.
- M8 checks recover Stokes slip, annular area, the single-tank implicit solution, exact generation stopping, zero-source/outflow limits and conserved solids volumes; shape/Re/inclination/non-Newtonian/dense cases remain conditional.
- M9 checks recover static zero and Joukowsky pressure before reflection; motion reversal changes pressure sign; pressure persists during a pipe pause. Conserved compressible storage, three-grid/time diagnostics, strict-tolerance failures, fixed-domain/diameter-transition gates and work bounds are verified.
- M10 checks recover vertical buoyant weight in four operation states, straight inclined pickup/slackoff/rotation friction, zero-friction curved-well TVD equilibrium, integration refinement, friction sensitivity, residual signs, compression and supplied-limit exceedance.
- API checks verify ownership/datum/original-source integrity, same-revision hydraulic links, immutable report inclusion, preserved source hashes and restart reopening.
- Windows locked an older dist/index.html during a rebuild. The blank/incomplete browser response was detected, not accepted as success. The repaired build writes a unique completed release and publishes a validated selector; active files remain untouched. The launcher/API select the same completed directory. Tests reject escaping and incomplete release pointers.

Chrome exercised the compiled app:

1. M7 calculated the original synthetic well stress/thermal scenario with 360 retained plotting points; selected coupled poroelasticity produced a saved withheld study. The original scenario reopened.
2. M8 created an explicitly synthetic Newtonian M6 source. The deviated original well withheld vertical transport at its inclination gate; the dedicated 1,000 m vertical fixture produced conserved generation/inventory/return histories and 40 depth intervals.
3. M9 saved the vertical piston motion response with 20/40/80 cells and the declared refinement tolerance satisfied. Swab speed reversal changed the response sign. A one-pascal refinement tolerance produced an explicit incomplete assessment.
4. M9 additionally saved a transient interval on North Sea · Research. Peak Reynolds was approximately 32.895, compressible-storage mass residual 1.821e-15 kg, and the declared numerical tolerance was met.
5. M10 vertical pickup recovered approximately 228.693 kN buoyant weight. Missing ratings were visible. An intentionally restricted one-kN surface rating produced an explicit exceeded-limit reason.
6. The original deviated well's rotating case saved 571 profile points, approximately 553.953 kN hookload and 6.364 kN.m surface torque. These are synthetic research results, not field validation.
7. Existing MSE saved a labelled surface proxy of approximately 356.07 MPa from the entered example inputs.
8. Saved studies reopened after the identity-checked service restart. At 390 px, document width was exactly 390 px; no error overlay or application browser error was observed in the completed app.
9. The UI created and displayed the fixed final report. Its preserved calculation models include casing, clustering, shaly_sand, em_vendor, hydraulics, stability, transport, surge-swab, torque-drag and mse; M1 remains a separate immutable engineering revision.
10. The live HTML, JS and CSS bytes match the selected release; health reports version 0.6.0, mode local-research and equipment_control false. Original sources and study bindings verified; the 51-entry audit chain reports verified.

Final served release: dist/release-6fe102c62455492293e1874fb57f8915.
Final JS: index-DgYH0hfj.js, SHA-256 f97e69ec9eb7b64eab34b92eab706a055c46839199de46ebdedab7e4aeaceb96.
Final CSS: index-COztpBjD.css, SHA-256 556b9b79d44041b0a6a073cf5c65c47a8d412b8f3dcde254d04e4009dbeefe93.

Report 7a89c96a-ce8d-486c-8424-57e0e6779d1d has canonical snapshot SHA-256 d612f6c6fbe8bbb485ff1823e8882348c6e7734bace86eff9a2cf77feaecc21a. The fixed exported evidence is evidence/modules1-10-report.json; live verification is evidence/modules1-10-live-verification.json. Screenshots are module7-stability.png, module8-transport.png, module9-surge-swab.png, module10-torque-drag.png, module10-mobile.png and module710-final-report.png.

The installation remains C:\Users\HP\OneDrive\Project Drill\geodrill-pro. Existing projects and prior reports were retained. MODEL-SPECS-0.6.md declares each reduced model and open qualification requirement. This evidence completes the software research-build task through M10; it does not qualify live operational use, native EM inversion, coupled geomechanics, cuttings beds, complete trip hydrodynamics or equipment control.

# Prior verification record — 3 October 2026 / version 0.5.0


## Added M6 evidence

- **200 automated tests pass**, including 52 new Module 6 cases. TypeScript compilation and the production build pass. The existing Starlette/httpx TestClient deprecation warning remains.
- Independent Poiseuille pipe/annulus and Buckingham–Reiner pipe cases match; Bingham annulus uses independently evaluated elementary antiderivatives; HB annulus is compared with an independent dense-grid velocity integration and quadrature refinement.
- Published Newtonian annulus parameters give 0.092393855 Pa/m versus the rounded published 0.09239. This is a kernel benchmark, not a profile applicability approval.
- A curved-well example has positive endpoint upper margins and a negative interior margin. The exact limiting MD is recovered from tangent-direction roots.
- Zero-flow/unyielded limits, horizontal-TVD head, bottom nozzle balance, specified mass continuity, segmented geometry, installed/planned separation, sensitivity and supply-rating comparisons are tested.
- Cases with stale/future/unknown mud evidence, unreviewed limits, unsupported circulation/effects, large Reynolds/roughness screens, tiny unresolved flow, mismatched datum and missing coverage abstain.
- Project ownership, historical/synthetic boundaries, original-source integrity, preserved calculations, restart and fixed-report inclusion are verified.

Chrome exercised the compiled workstation against the current local service:

1. Loaded labelled synthetic fluid, string/nozzle, pressure-window and supply-rating assumptions against saved M1 revision 30528304.
2. Saved the HB profile: 173 points, 58 hydraulic intervals and 16 admissible corners. Nominal losses were 0.528 MPa annular, 0.476 MPa pipe and 0.007 MPa nozzle; required supply 1.121 MPa included supplied upstream loss.
3. Changed circulation to multiphase; the saved result was withheld with its reason, and no profile plot was rendered.
4. Reloaded the app and reopened the original calculated study.
5. Edited a pressure-limit knot and verified its review state reset to unreviewed.
6. Verified the fixed report visibly contained steady-laminar-geometry-hydraulics and the original synthetic study.
7. At 390 px, document width remained 390 px; the original profile remained available. No application browser errors or Vite overlay were observed.
8. Cleared the optional supply rating using the focused input and keyboard, verified the field was empty, and saved Synthetic absent rating verified. The preserved input is null; the assessment is incomplete with its explicit reason and cannot claim inside tested bounds. An earlier empty-fill browser attempt retained 50 MPa and remains preserved in the audit trail.
9. Corrected a pressure editor accessibility label to name the displayed MPa unit, rebuilt successfully and retained final desktop evidence in evidence/module6-hydraulics.png.

Exact equations, domain limits, numerical tolerance and remaining qualification: MODEL-SPECS-0.5.md. These checks establish tested research software behavior; they do not qualify a mud system, operating pressure window, instrument error budget or field advisory system. Dependencies were unchanged.

# Previous Module 5 evidence — version 0.4.0

## Added M5 evidence

- **148 automated tests pass**, including 30 new Module 5 cases. TypeScript compilation and the production frontend build pass. The existing Starlette/httpx test-client deprecation warning remains.
- UTC-offset receipt-delay arithmetic and native-plus-offset MD alignment have independent expected-value checks. Boundary distances and tool-to-bit spacing remain unchanged by MD alignment.
- Contracts reject malformed units, timestamps, negative/zero resistivity, inconsistent parameter bounds, undocumented boundary references/misfit and repeated native depth.
- Unknown alignment, outside-survey samples, vendor-rejected/unknown quality and missing interpretations are withheld while preserving supplied evidence.
- Source/project identity, ownership, duplicates, wrong source type, synthetic/historical boundaries, raw/Parquet corruption, immutable calculations, restart and report inclusion are tested.
- Dependencies were unchanged. Earlier dependency-audit evidence remains historical.

Chrome exercised the compiled workstation against the running local service:

1. Loaded the labelled eight-sample EM interchange, with absent instrument/qualification metadata explicitly visible.
2. Saved a review displaying five supplied samples and withholding three: missing interpretation, rejected quality and unknown quality.
3. Set alignment unverified; all eight interpretations were withheld without plotting supplied points.
4. Reloaded the full app and reopened the original five-sample review.
5. Uploaded docs/examples/synthetic-em-vendor.json through the actual file control. Duplicate source bytes reused the original source and reset alignment/evidence.
6. Created a fixed report and verified both imported-vendor-em-review and synthetic-em-vendor.json in its visible report.
7. At 390 px, document width remained 390 px; no app browser errors or Vite overlay were observed.
8. Reviewed the desktop screenshot and refined the plot sizing; final screenshot is evidence/module5-em-vendor.png.

These checks verify the tested import/review software behavior, not the validity of a vendor earth model, instrument qualification or geosteering authority. Exact contract and remaining dependencies: MODEL-SPECS-0.4.md.

# Previous Module 4 evidence — version 0.3.0

## Added M4 evidence

- **118 automated tests pass**, including 25 new Module 4 cases. TypeScript compilation and the production build pass. Existing Starlette/httpx test-client warning remains.
- Source construction vertices M/D/S/Z and pure laminated limits are verified independently. Manually accounted dispersed and structural mixtures recover their known volumes.
- Two hundred deterministic independently generated forward mixtures verify conservation and that the original texture lies within the returned coexisting family.
- Tests retain nonuniqueness on the laminated line; handle zero-host normalization; reject apparent porosity, mismatched units, degenerate endpoints and inadmissible fractions; verify percent/fraction/GR equivalence; and exercise sensitivity changing branch and excluded corners.
- Raw/unknown correction states withhold interpretation. Missing observations and depths outside survey coverage remain withheld. Saved results retain raw/Parquet/geometry hashes, survive application recreation and remain in fixed reports after later source damage.

Chrome checked the compiled frontend with the actual local service:

1. Loaded the separate synthetic ten-sample PHIT/VSH source with explicit volume/endmember assumptions.
2. Saved eight admissible scenarios: five had nonunique textures. One sample was outside the model and one lacked porosity.
3. Verified the dispersed case at MD 2404: primary porosity 0.12; restricted laminated/dispersed/structural bulk volumes 0.4/0.06/0. The structural case at MD 2405 showed 0.24 primary porosity and 0.2/0/0.3 topology volumes.
4. Changed correction state to raw; all ten interpretations were withheld.
5. Reloaded the app and reopened the earlier eight-scenario study with its original evidence.
6. Changed the selected log; correction state reset to unknown and source-specific evidence cleared.
7. At a 390 px viewport, document width remained 390 px. No Vite error overlay or application browser errors were observed.
8. Created a fixed report containing the M4 source and complete calculation records.

Screenshot: evidence/module4-shaly-sand.png. Exact model conventions and limitations: MODEL-SPECS-0.3.md. These checks establish the tested software behavior, not petrophysical approval or field qualification.

# Previous implementation evidence — version 0.2.0

## Current software checks

- **93 automated tests passed** using the installed Python 3.12 runtime and isolated generated test-data directories.
- **TypeScript compilation and Vite production build passed**, including the M1/M2/M3 editors.
- A repeated Windows scheduling pause caused Hypothesis's one-second input-generation healthcheck to fail for the pre-existing scalar straight-survey property test. That generator timing check is now suppressed for that test only; all 100 generated examples and the displacement assertion remain enabled. The complete suite passes. No numerical failure was relaxed.
- One existing Starlette/httpx test-client deprecation warning remains; it does not affect the application request path.
- The build helper tools/build.py works after relocating the checkout. Dependency versions were unchanged; previous vulnerability-audit evidence below is dated, not a fresh audit.

## Added numerical/API coverage

M1: independent circular-arc interpolation, translated frames, small-angle limits, upturned two-crossing paths, tangent/coincident contacts, invalid/gapped/overlapping geometry, nested casing clearances, immutable revisions and stale-writer conflicts.

M2: independently computed thick-cylinder stress/von Mises result, equal hydrostatic principal stresses, wear and supplied derating, missing connection evidence, mandatory-case coverage, separately exceeded compression/connection limits and pipe-length cost scope. Numerically degenerate wall/rating/derating inputs are rejected.

M3: analytic separated responses and population variance/inertia, deterministic results, feature-order and descending-depth equivalence, training-only scaling, missing/out-of-envelope/out-of-survey rows, log10 back-transform, native-gap groups, degenerate features, known adjusted Rand partitions, exact unit matching and workload limits.

API checks preserve calculation and revision hashes, reject cross-project use and wrong datums, survive application recreation, block changed source bytes, and retain fixed report snapshots after later records or source damage.

## Current Chrome evidence

An isolated Chrome profile opened the compiled frontend against the actual local service.

1. M1 saved revision 30528304… with two hole sections, two nested synthetic casing records and four interpreted formation tops. 3D view, uncertainty bands and all four intersections rendered. Evidence: evidence/module1-geometry.png.
2. M2 loaded that revision, generated mandatory circulation cases, calculated the supplied synthetic pressures/forces and saved a conditional result. Both strings showed governing connection axial utilization 27.8%. A service restart retained the scenario; Open saved result displayed the original result. Evidence: evidence/module2-casing.png.
3. A fixed report retained the M1 revision SHA-256, M2 inputs and result. Later reports/revisions did not alter earlier report snapshots in API tests.
4. M3 saved the two-cluster GR/RHOB synthetic study: four eligible training samples, one missing-GR row withheld, response centers GR 46.5/84 API and RHOB 2.455/2.53 G/C3. Native-depth groups split around the missing row.
5. Requesting three clusters from the same four eligible samples produced insufficient_data with no cluster centers. The earlier two-group result reopened from the history. Evidence: evidence/module3-clustering.png.
6. Module 3 at a 390 px viewport had document width 390 px. No application browser errors or Vite overlay were observed.

These establish software behavior for the tested contracts; they do not establish field accuracy, geological interpretation validity, manufacturer qualification or a zero-error guarantee.

# Historical verification — 28 September 2026

## Software checks actually completed

- **52 automated tests passed** with Python 3.12 on this Windows workstation.
- **TypeScript compilation and Vite production build passed** after updating to Vite 6.4.3.
- Frontend `pnpm audit` (including development dependencies): **0 known vulnerabilities** reported by the registry on this date.
- Python `pip-audit` of the installed environment: **0 known vulnerabilities** reported on this date, after package updates.
- Python dependency consistency: no broken requirements found.

The Python test client emits one dependency deprecation warning about its use of `httpx`; it does not fail the tests or affect the application's request path. These tests use temporary, isolated data directories.

## Numerical and ingestion coverage

| Area | Verified cases |
|---|---|
| Trajectory | Vertical, straight inclined, analytic quarter-circle build, azimuth 359°→1° wrap, random straight displacement conservation, invalid/duplicate MD, antipodal rejection |
| MSE | Independent work/removed-volume calculation, pure axial limit, surface/downhole label, zero/low ROP withholding, unknown/off-bottom/connection states, strict types, finite inputs and minimum numerical diameter |
| Pressure | 1,000 m water-column analytical result 9.80665 MPa gauge; backpressure/annular-loss addition; equivalent-density reference; negative upper margin retained; invalid bounds, zero depth and unsupported regime rejected |
| Telemetry | SI/field conversion equivalence, missing values preserved, deliberate time gap, source state, unsupported units, missing timezone, duplicate timestamps, malformed headers, negative observations retained but ineligible, numeric conversion overflow |
| LAS | NULL sentinel preservation, curve metadata, depth unit handling; wrapped/unsupported units, duplicate depth and malformed row rejection |

## API and persistence coverage

- Missing session, cross-origin requests, cross-site API requests, untrusted hosts and missing mutation headers are rejected.
- No control command endpoint exists.
- Duplicate source import is idempotent; rejected imports do not register a dataset or append a successful audit event.
- Cross-project dataset access is rejected.
- Reports retain their exact snapshot after acknowledgement changes and after application re-instantiation.
- The report attachment endpoint returns the saved snapshot as JSON with a download filename.
- Report hashes are independently recomputed from canonical serialized snapshots in tests.
- Damaged Parquet or changed original source bytes block report generation; damaged Parquet blocks reads.
- SQLite refuses ordinary audit deletion; acknowledgement is idempotent.
- Oversized file upload, non-finite calculation values and extra request fields are rejected.

## Interactive workflow checked

The compiled frontend was exercised with the running local service, not a mock API:

1. Loaded the synthetic well and its three source files.
2. Calculated MSE from 110 kN WOB, 8 kN·m torque, 120 rpm, 28 m/h and 8.5 in diameter: **356.07 MPa surface proxy** displayed.
3. Changed ROP to zero: **withheld**, with no numeric MSE, displayed.
4. Calculated the 2,400 m, 1,250 kg/m³ pressure case with 1.5 MPa supplied loss: **30.920 MPa gauge**, equivalent density **1,313.7 kg/m³**, margins **4.920 MPa** and **7.080 MPa** displayed, with single-point applicability labels.
5. Acknowledged the intentionally missing SPP event with a development-test note; the original event and data remained present.
6. Created a fixed evidence report, restarted the actual service, and reopened that saved report from the report library.
7. Uploaded the duplicate synthetic telemetry file through the built-in browser; the UI confirmed that no duplicate was added.
8. Checked field-unit values in Chrome: the same measured depth displayed as 9,331.7 ft and MSE metric as 65.82 ksi; source storage remains SI.
9. Checked source-time playback controls and field/metric switching.
10. Checked desktop and 390-pixel narrow layout for document overflow; the narrow document width was 375 px within the 390 px viewport. Tables have their own horizontal scroll containers.
11. Downloaded the saved report in the built-in browser and parsed the 117,630-byte file. Its report ID, SHA-256, and three preserved datasets matched the reopened snapshot. The restarted local server independently returned HTTP 200 and the expected JSON attachment header.

Chrome now opens the app. Its automated file upload was blocked by the extension's file-access permission; that setting was not changed. Its download-event automation also did not observe the report save. The built-in browser completed both file workflows.

## Not demonstrated

No independent petroleum-engineering review, field data validation, blind-well validation, live-source qualification, uncertainty calibration, performance/soak qualification, accessibility conformance certification, formal penetration test, full disk/power-failure injection, signed installer qualification, or rig integration has been completed.

The example results and automated checks establish software behavior in the tested cases. They do not establish operational accuracy, equipment safety, API/ISO/IEC compliance or a zero-error guarantee.
