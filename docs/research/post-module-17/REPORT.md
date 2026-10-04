# GeoDrill Pro: post-Module-17 capability and advancement research

Research date: 4 October 2026, Asia/Jakarta. Baseline: GeoDrill Pro 0.8.0, audited offline MVP/research scope. Project: C:\Users\HP\OneDrive\Project Drill\geodrill-pro.

## Recommendation

Advance GeoDrill into a connected engineering review workstation: reconcile incoming data, group calculations into comparable scenarios, carry their dependencies into a drilling programme, and produce a readable review package. Add daily activity/cost reporting and read-only industry data exchange next. Broaden directional and drilling physics only with independent benchmark and experimental evidence.

The 17 module workflows are implemented at their declared research scope. Their breadth is useful, but professional adoption depends on the tasks between calculations: choosing authoritative inputs, managing revisions, comparing alternatives, reviewing assumptions, reporting daily performance and transferring evidence between people and systems. This conclusion is a product-design inference from the implementation and primary sources; it is not validated purchasing demand.

First tranche: GD-A01–A05. Deliver one complete path from mixed-format inputs to baseline/alternative studies to a frozen, reviewable programme pack. Keep experimental validation work visible from the first tranche. The full [backlog](BACKLOG.md) gives problem, solution, value hypothesis, dependencies, risks, acceptance and validation for 19 entries. [BACKLOG.csv](BACKLOG.csv) is the editable planning version; [IMPLEMENTATION-SEQUENCE.md](IMPLEMENTATION-SEQUENCE.md) contains release gates; [INTERVIEW-GUIDE.md](INTERVIEW-GUIDE.md) tests the demand hypotheses.

## 1. Completion trigger and inspection method

The original chat “Start building GeoDrill Pro”, 01a0e1de-6f67-7831-b058-523182f788ed, has a completed final turn and a delivery statement through Module 17. This was checked against [MODULES-1-17.md](../../MODULES-1-17.md), [VERIFICATION.md](../../VERIFICATION.md), versioned model specifications, and [live release evidence](../../evidence/m1217-live-verification.json). An idle chat or roadmap was not used as acceptance evidence.

The final delivery records report 406 passing tests, including 102 added for M12–M17; TypeScript and production compilation; Chrome input/import/save/reopen checks; a real restart preserving saved studies; five report snapshots and a 110-entry hash-linked audit chain. The [integrated report](../../evidence/modules1-17-report.json) freezes the preserved work through M17. These are inspected release records, not a new full test-suite run during this research.

Fresh read-only checks confirmed /api/health version 0.8.0, local-research, equipment_control false and PID 40440. Served JavaScript and CSS hashes matched the final release evidence. A separate Chrome session/profile opened the application, navigated to M15, reopened the saved “Synthetic flow gaps and interrupted persistence” study, navigated to Reports and reopened its existing fixed report. No study was recalculated, source imported, project created or report generated during this inspection. The research browser was closed afterward. The original browser session and service were not changed. Research evidence is in [RESEARCH-EVIDENCE.json](RESEARCH-EVIDENCE.json); [the inspection image](flow-research.png) accompanies it.

Implementation inspection covered services/api/main.py and storage.py, desktop geometry/hydraulics/report/research components, engineering model code and declared model limits. Absence findings below mean a workflow was not found in those reviewed sources, current UI or delivery scope; they do not claim that every possible hidden dependency has been exhaustively audited.

Source research used operator, association, standards-publisher, technical-committee, regulator and vendor primary pages. All material sources are logged with dates, limitations and claim support in [SOURCES.md](SOURCES.md). No engineer interviews, outreach, trials, enrollment, purchases or commercial forms occurred. No application code was modified.

## 2. Evidence categories

| Category | Meaning in this review |
|---|---|
| Implemented | Reachable UI/API workflow, typed contracts and persistence exist. |
| Numerically/software verified | Analytical/manufactured examples, numerical diagnostics, contracts and workflow checks pass within declared scope. |
| Experimentally validated | Independent measured data show acceptable performance within a specified physical envelope. Not established by the synthetic examples in this release. |
| Field-qualified | Intended use, representative operating conditions, human procedures and independent assurance have been assessed. Not established by this release. |
| External/supplied | Imported metadata or flags are preserved; authenticity and correctness are not independently proved by importing them. |
| Withheld | Missing or unsupported evidence prevents an assessment; this is a valid result. |
| Excluded | Autonomous equipment writes and actual rig-control authority remain outside scope. |

The remaining qualification includes instrumented BHA data, independently inspected bit cohorts, material/fluid wear programmes, adjudicated anomaly data, actual-mud PVT/flow-loop cases and model-specific engineering review. A small equation residual does not measure field predictive error. An immutable local hash chain demonstrates internal integrity checks; it is not independently witnessed identity or a regulated electronic signature.

## 3. Drilling-engineer decision and workflow map

Aramco’s current engineering role explicitly includes preparing drilling programmes, supporting operating divisions, penetration-rate studies and complex well engineering. That supports the scope of tasks in this map, without establishing demand for GeoDrill. [S01: Aramco — Senior Drilling Engineer, requisition 17894](https://careers.aramco.com/expat_uk/job/Senior-Drilling-Engineer/857223923/)

Norway provides a concrete jurisdictional example: programme preparation/update, collecting drilling data to check prognoses, and documented barrier status at handover. Those requirements inform document and evidence design; local jurisdiction and company requirements still need their own review. GeoDrill is not declared compliant merely because it stores a report. [S11: Havtil — Activities Regulations §81, Well programme](https://www.havtil.no/en/regulations/all-acts/the-activities-regulations3/XV/81/) [S12: Havtil — Activities Regulations §84, Monitoring well parameters](https://www.havtil.no/en/regulations/all-acts/the-activities-regulations3/XV/84/) [S13: Havtil — Activities Regulations §85, Well barriers](https://www.havtil.no/en/regulations/all-acts/the-activities-regulations3/XV/85/)

| Phase / decision | Needed inputs and handoff | Current support | Product gap / priority |
|---|---|---|---|
| Planning: select trajectory and target | Offset wells, target constraints, CRS/datum/north, survey tool uncertainty, hazards | M1 accepted-survey reconstruction, interpreted formation tops and casing geometry | Target/path designer, typed geodesy, uncertainty and multiwell clearance; A10 |
| Planning: select casing and programme | Loads, connections, ratings, barriers, cement, pressure/temperature bounds, reviewer | M2 restricted material/rating screens, M6/M7 research scenarios | Programme, load interaction, cement and barrier evidence; A03/A13 |
| Planning: choose mud, hydraulics and cleaning | Measured rheology, temperature/pressure, flow, nozzles, particle/bed response | M6 laminar hydraulics and M8 dilute near-vertical transport | Broader validated closures and usable scenario comparisons; A02/A11 |
| Planning: BHA, bit and string selection | Tool dimensions/ratings, offset runs, friction, dynamics measurements | M10–M14 declared research models and supplied records | Calibrated mechanics/response, inspected comparable cohorts; A12/A15 |
| Execution: verify actual versus programme | Well/section identities, source and receipt times, revised inputs, readings and decisions | Historical telemetry replay, event acknowledgement, immutable studies | Read-only exchange, currentness and dependency status, programme change review; A01/A02/A07/A09 |
| Execution: diagnose balance or performance change | Native measurements, transfers, stock, rig context and reference events | Surface MSE proxy, M15 causal offline balance replay | Calibrated source integration and independently adjudicated evaluation; A16 |
| Tripping/casing/completion preparation | Current string/casing, motion and pressure boundaries, loads, barrier test evidence | M9/M10/M11 and restricted M14 | Variable-geometry transient, calibrated loads, documented barrier handover; A12/A13 |
| Daily reporting: explain time and cost | Activity intervals/codes, NPT reasons, budget/actual, reviewers | Events and fixed generic research reports | Structured DDR, interval reconciliation, cost/variance workflow; A06 |
| Post-well: learn and compare | Comparable offsets, complete activities, run outcomes, lessons and exclusions | Individual project studies, M13 descriptive cohorts, snapshots | Cross-well comparable section analysis and lessons; A14 |
| Cross-cutting: review and recover work | Traceable sources, roles, revision decisions, restore evidence | Local session boundary and internal hashes | Named review identities, conflict handling, backup/restore and packaging; A08/A09 |

These workflow requirements also align with documented industry reporting and data-quality concerns. IADC DDR Plus provides a granular reporting codeset/schema; its reporting classifications must not be treated as instantaneous machine states. The historical DSABOK document records disagreements and concerns about clocks, delayed data, source calibration, identifiers and code granularity, rather than a universally agreed implementation. [S02: IADC — DDR Plus v2](https://iadc.org/ddrplus/) [S10: DSABOK — Drilling Automation Pain Points and User Stories v0.1](https://dsabok.org/wp-content/uploads/2020/08/Drilling-Automation-Pain-Points-and-User-Stories-V0.1-released.pdf)

## 4. Capability and gap matrix across all 17 modules

Local evidence for M1–M10 is [MODULES-1-10.md](../../MODULES-1-10.md); M11 is [MODULES-1-11.md](../../MODULES-1-11.md); M12–M17 are [MODULES-1-17.md](../../MODULES-1-17.md) and [MODEL-SPECS-0.8.md](../../MODEL-SPECS-0.8.md). Earlier module equations remain in MODEL-SPECS-0.2 through 0.7. Every row describes a delivered research workflow, followed by its scope limitation and proposed advancement.

| Module | Delivered capability and evidence | Gap relevant to engineering work | Next upgrade / validation gate |
|---|---|---|---|
| M1 Geometry | Minimum-curvature accepted-survey geometry, formation intersections, local coordinates, interpreted surfaces and immutable revisions; analytical/browser evidence | Free-text coordinate frame is not a CRS transformation; survey uncertainty unquantified; no target-constrained path designer or multiwell collision analysis | A10: typed geodesy/tie-in and covariance diagnostics before clearance research |
| M2 Casing | Programme editor, body/connection records, mandatory loads, Lamé/von Mises and supplied-rating screens, loss allowance and uniform derating | Restricted combined mechanics; supplied ratings require verification; no complete cement/barrier programme or qualified design approval | A13: independently checked interaction/load cases and barrier evidence |
| M3 Log clustering | Native-depth LAS features, exact units, training-only normalization, seeded k-means, stability and eligibility records | Clusters have no validated facies meaning; environmental correction, noise/domain-shift and held-out labels limited | A05/A15: reviewed corrections and labelled independent wells; preserve exploratory status |
| M4 Shaly sand | Wet-shale/porosity scenarios, nonunique alternatives, parameter corners and plots | Endmembers/corrections require compatible core/image-log calibration; unequal-property extensions absent | A05/A17: core/log comparisons and supported property ranges |
| M5 EM | Vendor-result import/review, native MD/units/time and supplied intervals/misfit with hashes | Actual vendor adapters, calibrated measurements and independent uncertainty checks missing; no native EM inversion | A01/A07 plus separately licensed external vendor integration; inversion requires new qualified project |
| M6 Hydraulics | Steady laminar Newtonian/Bingham/Herschel–Bulkley pipe/concentric-annulus pressure profiles, equipment and mud records, corners and gates | Common turbulent, eccentric, rotating, cuttings, P/T and transient effects excluded; supplied pressure window is not an approved envelope | A11: characterized flows and independently measured pressure residuals |
| M7 Stability | Isotropic Kirsch wall stress, restrained thermal estimate, strength screens/refinement and supplied bounds | Anisotropy, plasticity, fracture and coupled pore/thermal diffusion absent; stress/strength inputs uncalibrated | A17: reviewer-selected models plus measured/core-supported cases |
| M8 Transport | M6-linked near-vertical dilute spherical Stokes transport, inventories, return/conservation and refinement | Deviated beds, hindered/non-Newtonian settling, particle distribution, rotation and turbulence absent | A11: flow-loop/solids-return comparisons over declared angles and fluids |
| M9 Surge/swab | M6-linked uniform-annulus acoustic piston replay, motion history, pressure limits and refinement | Variable geometry/internal-fluid boundaries, gels, gas/cavitation and nonlinear compression limited | A12: independent variable-geometry transient reference and field error budget |
| M10 Torque/drag/MSE | Geometry-linked quasi-static soft-string loads, friction ranges, residuals and mesh checks; state-gated surface MSE proxy | No independent friction/bias calibration; stiffness, end-force and dynamics limits remain | A12: operation-specific fitting and blind runs; never treat surface MSE as measured bit energy |
| M11 Buckling | Bound M10 inputs, plain-pipe sinusoidal/helical thresholds, effective-force declarations and conditional axial transfer | Straight/inclined nonrotating assumptions; curved transitions/joints/stabilizers withheld; no full 3D contact solver | A12/A15: independently reviewed mechanics and experiments before expansion |
| M12 Dynamics | Three-coordinate straight cantilever dynamics, modal/energy/refinement checks and separate supplied acceleration review | Generalized modes are not observed spatial BHA modes; calibration/observability/full-contact evidence missing | A15: calibrated bandwidth-qualified instrumented BHA benchmark |
| M13 Bit condition | Bit identity, inspected failure/censor evidence, availability cutoff, descriptive survival and conditional cost | Informative censoring, small/nonrepresentative cohorts; no calibrated individual remaining life or trip recommendation | A15: prospective inspected cohorts and held-out evaluation before predictive claims |
| M14 Wear/fatigue | Contact exposure, material coefficient wear, separate S–N/Miner accounting, inspection residuals and uniform-wall screen | Grooves, missing exposure, corrosion, cracks/load sequence and qualified residual capacity limited | A13/A15: material/fluid wear programme and inspection comparisons; keep barrier approval separate |
| M15 Anomalies | Native control-volume mass-balance replay, unknown intervals, persistence reset and event metrics | Supplied calibration/labels not authenticated; no demonstrated field early-kick performance or live operational alarm | A16: causal field holdout plus monitored-hour false-candidate/miss/latency accounting |
| M16 Gas/phase | Characterized nonpolar binary PR equilibrium, external mud-phase review and conserved batch relaxation | Binary EOS is not actual drilling-mud solubility; supplied flags not independently verified; no full multiphase wellbore energy/momentum/slip | A17: laboratory actual-fluid data and independently qualified solver/adapter |
| M17 Supervisory research | Isolated first-order pressure plant/PID and independent simulated request gates, expiry/fault/manual override | Logical simulation lease is not an operator/OEM equipment authorization; no hardware or network adapter | Preserve simulator only, A19 excluded; offline experiments can continue without control authority |

### Scope implications

Advanced engineering work cannot be unlocked solely by changing a withholding condition. The unsupported model needs a defined physical formulation, independent verification, representative validation and an intended-use review. This is particularly material for anti-collision, hole cleaning, early-kick interpretation and remaining-life estimates.

The application already has useful strengths: explicit unknown states, immutable revisions, original/source hashes, model versions, input/source matching and unsupported-state explanations. Keep those while adding workflow convenience. A09 review attestation should preserve engineering accountability without pretending that the current actor label or session cookie authenticates an engineer.

## 5. Competitor comparison

The following are capabilities documented by the vendors on pages inspected on the research date. No hands-on trials, price comparison, numerical performance benchmark, market-share verification or procurement conclusion was performed.

| Product | Documented workflow | GeoDrill comparison / inference |
|---|---|---|
| SLB DrillPlan | Shared design editing, automatic dependency management, coherent geometry/activity design, validation and programme reporting | A02/A03/A09 address a clear workflow gap. Matching advertised algorithm counts is not a meaningful acceptance target. [S05: SLB — DrillPlan](https://www.slb.com/products-and-services/delivering-digital-at-scale/software/delfi/delfi-solutions/drillplan) |
| Halliburton COMPASS | Trajectory planning, surveys, anti-collision, look-ahead and EDM integration | M1 provides a starting geometry record; it lacks the directional planning/uncertainty/multiwell workflow. A10 is a specialist expansion. [S06: Halliburton — COMPASS](https://www.halliburton.com/en/products/engineers-desktop-suite/compass-software) |
| Halliburton WellPlan | Broader hydraulics/hole-cleaning, torque/drag, BHA analysis, surge/swab and related string-operation analysis | M6/M8–M12 have narrower declared formulations. A11/A12/A15 require new evidence, rather than claims of present equivalence. [S07: Halliburton — WellPlan](https://www.halliburton.com/en/products/engineers-desktop-suite/wellplan-software) |
| Halliburton OpenWells | Structured operations reporting, EDM sharing, rulebooks, NPT and offset-section analysis, external source imports | A06/A14 fill daily/post-well workflow gaps beyond current event acknowledgement and research reports. [S08: Halliburton — OpenWells](https://www.halliburton.com/en/products/digital-well-operations/openwells-software) |
| Peloton WellView | Lifecycle records, activity/cost linkage, schematics, role-specific views and enterprise integrations | A03/A06/A08/A09 address continuity and adoption. GeoDrill has an offline local research baseline; enterprise deployment has not been demonstrated. [S09: Peloton — WellView](https://www.peloton.com/products/well-data-lifecycle/wellview) |

A plausible initial positioning is “transparent, reproducible drilling engineering review with explicit model applicability.” Hypothesis H10: some small engineering teams, consultants or training groups may value that focus. Their need, budget, preferred deployment and willingness to substitute or complement existing tools are untested. Do not claim replacement of the established products from feature-page comparison.

## 6. Integration, usability and deployment findings

### Data exchange

The implemented importer has a 2 MiB file limit (services/api/main.py:40, 133–135, 371–372), original bytes and normalized records, and explicit geometry/source bindings. This is a bounded import workflow. A07 should introduce a separate read-only adapter without expanding equipment authority.

Energistics’ current top-level guidance pairs WITSML 2.1 with ETP 1.2 and Energistics common 2.3. Pin actual released schema packages and supported objects; separately document mappings for legacy customer feeds. The page contains older contradictory recommendations in historical sections and pending JSON-schema language, so do not treat every section as a current implementation requirement. [S03: Energistics — WITSML Developers & Users](https://energistics.org/witsml-developers-users)

Account for well/wellbore identity, units, timezone, acquisition/receipt/availability time, clock drift, delayed downhole channels, duplicates, corrections and reconnect gaps. Preserve raw records and map each transformation; never interpolate missing data merely to make a plot continuous. Derived alignment must show its uncertainty and source interval. These are design requirements inferred from the data quality evidence and present product limits.

### User experience

The fresh M15 inspection showed a long per-sample form and a useful preserved result. ResearchStudy.tsx limits editable displayed lists to 24 records while retaining all data; large imports therefore need searchable, paginated tables and error navigation. The overview's lack of telemetry in a synthetic module project can be explained with an explicit “study-only project” state rather than leaving users to infer why replay is disabled.

main.tsx:29–31 and 170 implement a generic JSON-style print summary, with arrays shortened to the first eight displayed records and a complete JSON download. That is an honest research export; it is not a finished drilling-program or daily-report document. A03 should preserve full annexes and generate decision-oriented sections: scenario choice, differences, assumptions, excluded calculations, required evidence and reviewer disposition.

The app has Metric/Field presentation controls, but no complete all-module unit-profile validation was performed in this research. Treat consistency across every research editor/plot/export as an acceptance task, not a confirmed conversion bug. Repeated form values such as 0.10000000149011612 appeared in the M15 snapshot; A04 should distinguish numeric storage precision from readable display precision.

### Collaboration and recovery

main.py:48 creates a per-process local token; the boundary handles host/origin/local session access. Reviewed storage tables provide projects, datasets, events, studies, reports and audit records, but do not implement a named-user permission/review-signature workflow. Review acknowledgements should not be described as operator approval.

main.py:46 defaults data to ROOT/data unless GEODRILL_DATA_DIR is set; the installation is under OneDrive. The live data-directory setting and cloud synchronization behavior were not determined here, so synchronization damage is not alleged. A08 should inspect the selected active data path, provide an appropriate local writable location and verify SQLite-consistent backup/restore on a clean machine. An error that suggests restoring from backup is not evidence of an implemented recovery wizard. Network/team deployment needs a separate security and identity design.

## 7. Priority rationale and implementation sequence

Priorities are qualitative engineering/product judgments, not measured ROI. P0 establishes coherent and reviewable use of current work; P1 adds professional workflows and core engineering coverage; P2 requires more specialized data and validation. Relative effort S/M/L/XL is an initial sizing hypothesis, not a schedule or quote.

1. **Tranche 1 — useful review workflow:** A01, A02, A03, A04 and A05. Use one representative project with mixed units and missing data, a baseline and two alternatives, one revised geometry and one withheld calculation. Exit only when an independent reviewer can reproduce the chosen case and identify stale/excluded evidence from the pack.
2. **Tranche 2 — delivery data:** A06, A07 and A08, then A09 before multiuser/network exposure. Provide daily reconciled activities/costs, read-only exchange, recovery and named review handoffs.
3. **Tranche 3 — validated core physics:** A10, A11 and A12 in separate model programmes. Sequence each expansion by available independent data and intended-use review. A13 connects casing/cement/barrier documentation; it does not automate barrier approval.
4. **Tranche 4 — specialist evidence and learning:** A14–A18. Cohorts, BHA, anomaly and fluid work are distinct validation programmes. Introduce evidence search only after permissions and source/revision handling are reliable.
5. **Excluded — rig actuation:** A19 remains excluded. Preserve equipment_control false; no OEM interface, PLC write or operational lease is needed to finish this roadmap's research scope.

If the first interviews show that teams mainly need DDR rather than programme authoring, move A06 ahead of the broader A03 document template after the data foundation. If directional contractors are the initial users and can supply benchmark data, prioritize A10 earlier. This conditional ordering avoids assuming every drilling-engineer segment has the same daily problem.

## 8. Validation and data programme

ISCWSA provides published survey-error diagnostics and test-well spreadsheets suitable for independent benchmark construction. Pin revision/toolcode, covariance conventions and correlation assumptions; comparison to those examples does not establish a universal safe separation criterion. [S04: ISCWSA — Error Model Documentation](https://www.iscwsa.net/error-model-documentation/)

Equinor's historical Volve field release is a candidate for identity mapping, retrospective reports and data-import evaluation. Its current data-sharing page points to Databricks Marketplace. Access, license suitability, completeness, labels and sampling must be checked for each proposed dataset. Historical offshore wells do not automatically qualify a new model for unrelated fluids, rigs or formations. No data access account or download was initiated here. [S14: Equinor — Data sharing](https://www.equinor.com/energy/data-sharing) [S15: Equinor — Volve dataset](https://www.equinor.com/energy/volve-data-sharing)

For each model upgrade: freeze the physical scope; define measured reference quantities and tolerances before fitting; distinguish training and held-out wells/runs; record missingness and sensor uncertainty; independently reproduce at least one analytical/reference case; quantify model residuals by operating regime; report every excluded case; and get a qualified reviewer to assess intended use. For anomaly work, count false candidates per valid monitored hour and disclose missed/adjudication-uncertain events and latency distributions. For bit cohorts, inspect censoring mechanisms before interpreting survival or cost curves. For phase/transport models, conservation and convergence are necessary numerical checks, followed by independent physical comparisons.

A later document-search experiment has operator-authored precedent: Equinor's 2026 Ask Volve brief describes information spread across reports/spreadsheets and asks for answers with source/page citations. A18 remains a demand hypothesis until engineering users complete representative lookup tasks. [S16: Equinor — Ask Volve, 2026 industrial hackathon brief](https://github.com/equinor/industrial-hackathon-2026/blob/main/ask-volve/README.md)

## 9. Demand hypotheses to test

| Hypothesis | Current evidence | What would change the roadmap |
|---|---|---|
| H1: source reconciliation/re-entry is a frequent pain | Standards/user stories and current manual imports | Observed frequency, error/rework examples, permitted sample files |
| H2: scenario consistency and review packs are valuable | Vendor dependency workflows; operator programme task | Last real review with revision errors; required template and reviewer behavior |
| H3: large-form/table improvements save review effort | Fresh UI inspection; vendor UX emphasis | Timed tasks and error discovery by representative users |
| H4: DDR/cost/post-well linkage has useful value | IADC schema and operations-product workflows | Actual reporting cadence, ownership, code definitions and reconciliation effort |
| H5: local/offline deployment and recoverability suit an initial segment | Present architecture; product inference | IT restrictions, device/network policy, collaboration requirements |
| H6: directional users need uncertainty/clearance | ISCWSA/COMPASS scope | Tool-specific models, offset availability and responsible reviewer |
| H7: hydraulics/cleaning/mechanics breadth is the next core need | Present limitations and broader vendor coverage | Ranked real calculations plus independently measured cases |
| H8: casing/barrier evidence handover matters | Jurisdictional example and product gap | Applicable local rules, company templates and evidence owner |
| H9: cited evidence retrieval helps | Operator hackathon brief | Real questions, answer verification behavior and task-time comparison |
| H10: transparent research review is commercially attractive | Positioning inference only | Segment interviews, procurement constraints and controlled pilot outcomes |

No hypothesis is an established customer demand, willingness-to-pay finding or commercial forecast.

## 10. Recommended next development brief

Build a “programme review” workflow around one existing project. The user maps source fields and units, sees readiness/unknowns, creates linked baseline/alternative study bundles, changes a geometry revision and sees dependent results marked stale, selects the appropriate case and exports a complete evidence-linked review pack. Review status is tied to the frozen revision, with its qualified-use status visible.

Acceptance demonstration: independent reviewer imports the pack into an isolated workspace, reproduces eligible calculations, sees the same withheld cases, checks all source/model hashes, locates the basis for the chosen alternative and identifies missing field evidence. No operational approval or equipment command is generated. Only after this gate should scope expand to daily reporting and data exchange.

This review completes the requested research deliverables. It does not implement the advancement backlog. The current application and its equipment-control boundary remain unchanged.
