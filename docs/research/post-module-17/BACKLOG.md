# Prioritized advancement backlog

Prepared 4 October 2026. Baseline 0.8.0; proposed work only. Priority is an informed judgment, not measured ROI. Effort S/M/L/XL is relative sizing, not a duration estimate. H1–H10 are unvalidated demand hypotheses in REPORT.md. Source IDs resolve in [SOURCES.md](SOURCES.md). [CSV](BACKLOG.csv) retains the same complete fields for planning.

## GD-A01 — Data readiness and import mapping

- **priority:** P0
- **capability:** Data readiness and import mapping
- **user problem:** Engineers spend time reconciling units, aliases, datums and missing channels.
- **proposed solution:** Versioned field mapping, source dictionary, coverage/quality panel, bulk import with quarantine and larger bounded streaming file handling.
- **expected value or hypothesis:** Less manual reconciliation; hypothesis H1.
- **dependencies and data:** Existing provenance contracts; sample operator files.
- **engineering or data risks:** Unit confusion, schema drift, memory limits.
- **acceptance criteria:** Original bytes immutable; every mapping stores version and units; unknown datum blocks geometry binding; duplicate imports idempotent; proposed 100 MiB import fixture completes within a documented workstation memory budget.
- **validation method:** Golden mixed-unit/alias/missing fixtures; invalid source rejection; memory and cancellation tests; compare mapped values with source rows.
- **relative effort:** M
- **sources:** S03,S10
- **depends on:** None

## GD-A02 — Study dependency and scenario management

- **priority:** P0
- **capability:** Study dependency and scenario management
- **user problem:** Changing geometry or mud can leave comparisons tied to different assumptions.
- **proposed solution:** Scenario bundles, lineage graph, baseline/alternative comparison and stale-result notices.
- **expected value or hypothesis:** Fewer inconsistent design comparisons; H2.
- **dependencies and data:** GD-A01; immutable existing revisions.
- **engineering or data risks:** Accidental overwrite or silently recomputing old studies.
- **acceptance criteria:** Geometry/mud/source change identifies every dependent result; immutable old snapshots remain readable; comparison names all differing inputs and models; no stale result labelled current.
- **validation method:** Change one shared input; trace M6→M8/M9 and M10→M11; golden lineage and UI tests.
- **relative effort:** M
- **sources:** S05
- **depends on:** GD-A01

## GD-A03 — Drilling-program and review pack

- **priority:** P0
- **capability:** Drilling-program and review pack
- **user problem:** Raw study JSON is hard to turn into a reviewed programme.
- **proposed solution:** Revision-controlled section/activity plan, assumptions and hazard register, selected-study references, human review states, readable PDF/HTML and CSV exports.
- **expected value or hypothesis:** Reviewable handoff from planning to execution; H2.
- **dependencies and data:** GD-A02; agreed programme template.
- **engineering or data risks:** Draft may be mistaken for operator approval; truncated output.
- **acceptance criteria:** Each programme freezes source/model hashes; unsupported scopes conspicuous; reviewer comments refer to exact revision; generated document includes complete selected tables or explicit linked annexes; research-only watermark until qualification.
- **validation method:** Independent reviewer rebuilds two scenarios from exported inputs; compare report/source hashes; test export pagination and missing-evidence disclosure.
- **relative effort:** M
- **sources:** S01,S05,S11
- **depends on:** GD-A02

## GD-A04 — Usability for large records and units

- **priority:** P0
- **capability:** Usability for large records and units
- **user problem:** Long repetitive forms and generic outputs slow review.
- **proposed solution:** Searchable paginated record tables, column validation, chart detail inspection, labelled unit profiles and keyboard navigation.
- **expected value or hypothesis:** Faster error discovery; H3.
- **dependencies and data:** GD-A01; representative tasks.
- **engineering or data risks:** Conversion round-off; hidden off-page errors.
- **acceptance criteria:** All records searchable/exportable; error links open exact row; supported unit conversions round-trip within numerical tolerance; unknown values never become zero; keyboard completes critical review path.
- **validation method:** Task-based usability study; large-list fixtures; unit round-trip tests; accessibility review and 390 px checks.
- **relative effort:** M
- **sources:** S09
- **depends on:** GD-A01

## GD-A05 — Qualification ledger and reference cases

- **priority:** P0
- **capability:** Qualification ledger and reference cases
- **user problem:** Users need to distinguish calculation checks from physical evidence.
- **proposed solution:** Per-model applicability card, verification cases, data rights, reviewer signoff and qualification status.
- **expected value or hypothesis:** Credible use boundaries and release claims.
- **dependencies and data:** Existing model specs and evidence records.
- **engineering or data risks:** Benchmark leakage; overclaiming validated range.
- **acceptance criteria:** Every model lists supported/withheld states and benchmark provenance; analytical, experimental and field statuses separate; all reported tolerances approved before validation; no synthetic case presented as field evidence.
- **validation method:** Independent reference recomputation; reproducible benchmark manifest; deliberately out-of-scope cases withhold.
- **relative effort:** S
- **sources:** S04,S10
- **depends on:** None

## GD-A06 — DDR and activity/cost reporting

- **priority:** P1
- **capability:** DDR and activity/cost reporting
- **user problem:** Operations and costs are disconnected from calculation studies.
- **proposed solution:** Daily activity timeline, NPT annotations, section/day cost ledger, budget versus actual, variance explanations and structured DDR exchange.
- **expected value or hypothesis:** Connects engineering decisions to delivery performance; H4.
- **dependencies and data:** GD-A01–A03; licensed taxonomy and operator definitions.
- **engineering or data risks:** Overlaps, timezone errors, inconsistent NPT/currency meanings.
- **acceptance criteria:** Each reporting day reconciles elapsed intervals with explicit gaps; overlaps flag; actual/planned costs and currency date explicit; NPT classification retained with author and reason; XML validates against approved selected DDR schema.
- **validation method:** Hand-calculated 24 h case with gaps/overlaps/DST; cost reconciliation; schema round-trip; compare with existing operator DDR.
- **relative effort:** L
- **sources:** S02,S08,S09
- **depends on:** GD-A01,GD-A03

## GD-A07 — Read-only WITSML/ETP integration

- **priority:** P1
- **capability:** Read-only WITSML/ETP integration
- **user problem:** Manual file imports cannot sustain site/office data exchange.
- **proposed solution:** Isolated read-only WITSML 2.1/ETP 1.2 adapter with source authorization, replay, deduplication and quality dashboard.
- **expected value or hypothesis:** Less re-entry; fresher auditable data; H1.
- **dependencies and data:** GD-A01/A05; released schemas and authorized test server.
- **engineering or data risks:** Ordering, reconnect loss, clock drift and vendor extensions.
- **acceptance criteria:** No equipment endpoint; raw/receipt/source time retained; reconnect/duplicate/out-of-order handling reproducible; schema and unit incompatibility quarantined; explicit stale marker; no fabricated sampling.
- **validation method:** Conformance fixtures plus independently authorized simulator interoperability; reconnect/backpressure soak; audit declared supported objects.
- **relative effort:** L
- **sources:** S03,S10
- **depends on:** GD-A01,GD-A05

## GD-A08 — Recovery, packaging and deployment

- **priority:** P1
- **capability:** Recovery, packaging and deployment
- **user problem:** A local release needs repeatable recovery and installation.
- **proposed solution:** Documented writable data location, SQLite-consistent backup/restore, portable evidence bundle, signed installer/update rollback and diagnostics.
- **expected value or hypothesis:** Lower installation/recovery friction; H5.
- **dependencies and data:** GD-A05; signing infrastructure if installer pursued.
- **engineering or data risks:** Cloud-sync concurrency; migration failure; lost attachments.
- **acceptance criteria:** Restore reproduces dataset/report hashes and audit chain on clean machine; migrations reversible; app code and writable data separately located; active DB location checked for sync hazards; no administrator rig privileges.
- **validation method:** Fresh Windows install/uninstall; crash during backup; restore/migration/rollback exercises; tampered bundle rejection.
- **relative effort:** M
- **sources:** Local code evidence
- **depends on:** GD-A05

## GD-A09 — Team identities and review workflow

- **priority:** P1
- **capability:** Team identities and review workflow
- **user problem:** A startup token does not identify accountable reviewers.
- **proposed solution:** Named identities, project access, optimistic conflict handling, reviewer/author roles and immutable revision attestations.
- **expected value or hypothesis:** Traceable human handoff; H5.
- **dependencies and data:** GD-A03/A08; deployment/threat model.
- **engineering or data risks:** Role bypass; signature over wrong revision.
- **acceptance criteria:** Review attestation binds exact content hash and identity; old decisions never transferred to revised content; unauthorized project access rejected; conflicts do not overwrite changes.
- **validation method:** Access/role matrix tests; concurrent revisions; independent security review before network deployment.
- **relative effort:** L
- **sources:** S05,S09
- **depends on:** GD-A03,GD-A08

## GD-A10 — Geodesy, survey uncertainty and anti-collision research

- **priority:** P1
- **capability:** Geodesy, survey uncertainty and anti-collision research
- **user problem:** A plotted centreline cannot quantify collision risk.
- **proposed solution:** Typed CRS/datum/north transformations, tie-in surveys, tool-error covariance and multiwell clearance research.
- **expected value or hypothesis:** Supports directional planning review; H6.
- **dependencies and data:** GD-A01/A05; ISCWSA/tool-provider models and geodetic references.
- **engineering or data risks:** Correlated error, convention mismatch, unqualified clearance.
- **acceptance criteria:** Coordinate round-trip and north conventions documented; covariance matches pinned ISCWSA diagnostic wells to predeclared component-wise tolerances; full correlation assumptions displayed; missing model withholds risk results; no drilling clearance issued.
- **validation method:** Independent geodetic cases; Rev5 spreadsheet comparisons; closest-approach edge cases; survey specialist review.
- **relative effort:** XL
- **sources:** S04,S06
- **depends on:** GD-A01,GD-A05

## GD-A11 — Operational hydraulics and hole cleaning

- **priority:** P1
- **capability:** Operational hydraulics and hole cleaning
- **user problem:** Laminar concentric and vertical dilute models exclude common wells.
- **proposed solution:** Versioned transition/turbulence and eccentric/rotating annulus closures; non-Newtonian, particle distribution and deviated-bed models.
- **expected value or hypothesis:** Broader M6/M8 usefulness within validated envelope; H7.
- **dependencies and data:** GD-A05; measured rheology/flow-loop/PWD datasets.
- **engineering or data risks:** Extrapolation, empirical closure error and coupled stability.
- **acceptance criteria:** Each closure declares calibration range; conservation and refinement pass; Newtonian limits recovered; independent flow-loop/PWD and solids-return residuals reported with predeclared acceptance/error budget; unsupported states remain gated.
- **validation method:** Analytical limits, mesh/time refinement, blind flow-loop cases stratified by angle/rheology/flow; engineering review.
- **relative effort:** XL
- **sources:** S07
- **depends on:** GD-A05

## GD-A12 — Calibrated torque/drag and trip studies

- **priority:** P1
- **capability:** Calibrated torque/drag and trip studies
- **user problem:** Friction ranges and simple transients do not capture all mechanics.
- **proposed solution:** State-specific friction fitting, bias separation, variable-geometry surge/swab and selected stiff-string/contact extension.
- **expected value or hypothesis:** Improved load/trip comparisons; H7.
- **dependencies and data:** GD-A02/A05/A11; reliable rig data.
- **engineering or data risks:** Identifiability, joint/end force/contact error.
- **acceptance criteria:** Calibration uses training runs only; blind residuals retained by operation/depth; μ and sensor-bias identifiability disclosed; M11 limits preserved unless new solver qualified; surge pressures checked against independent cases.
- **validation method:** Analytic equilibrium; cross-validation by well/run; blind loads; transient reference comparison with documented error budget.
- **relative effort:** XL
- **sources:** S07,S10
- **depends on:** GD-A02,GD-A05,GD-A11

## GD-A13 — Casing, cement and barrier evidence

- **priority:** P1
- **capability:** Casing, cement and barrier evidence
- **user problem:** Casing stress checks do not describe complete barrier readiness.
- **proposed solution:** Expanded qualified load cases plus component/cement catalogue, barrier schematic and test-evidence/handover ledger.
- **expected value or hypothesis:** Connects casing design to documented integrity review; H8.
- **dependencies and data:** GD-A03/A05/A09; manufacturer and jurisdiction-specific references.
- **engineering or data risks:** Misrepresented standards or test pass; evidence authenticity.
- **acceptance criteria:** Planned/installed/tested statuses distinct; expired/missing tests visible; cement and connection assumptions explicit; load interaction compared independently; no barrier or operational approval automatically generated.
- **validation method:** Reviewed catalogue references; missing/failed/expired barrier tests; independent casing solver cases; qualified well-integrity review.
- **relative effort:** XL
- **sources:** S11,S13
- **depends on:** GD-A03,GD-A05,GD-A09

## GD-A14 — Offset-well performance and lessons

- **priority:** P2
- **capability:** Offset-well performance and lessons
- **user problem:** Per-project studies cannot easily transfer lessons across wells.
- **proposed solution:** Searchable offset sections, comparable cohorts, lessons tied to source events, planned versus actual duration/cost.
- **expected value or hypothesis:** Post-well learning with transparent comparability; H4.
- **dependencies and data:** GD-A06/A07; harmonized taxonomy.
- **engineering or data risks:** Biased offsets; leakage; missing cost contexts.
- **acceptance criteria:** Comparisons show exclusions, section geometry, rig/mud/state differences and missing records; aggregate totals reconcile; retrospective report rebuilds from frozen inputs.
- **validation method:** Hand-checked multiwell corpus; reviewer audit of exclusions; avoid fitted universal technical-limit claims.
- **relative effort:** L
- **sources:** S08,S09
- **depends on:** GD-A06,GD-A07

## GD-A15 — Measured BHA and bit/wear qualification

- **priority:** P2
- **capability:** Measured BHA and bit/wear qualification
- **user problem:** Synthetic dynamics and descriptive cohorts cannot support field predictions.
- **proposed solution:** Instrumented BHA benchmarks; inspected bit-run cohorts; material/fluid wear tests and fatigue inspection comparisons.
- **expected value or hypothesis:** Evidence-based expansion of M12–M14.
- **dependencies and data:** GD-A05/A07; data rights, calibrated sensors and recovered inspections.
- **engineering or data risks:** Sampling aliasing, censoring bias, unavailable ground truth.
- **acceptance criteria:** Time/bandwidth/calibration reviewed; held-out wells/runs untouched; informative censoring analysed; uncertainty calibrated if predictive claims pursued; wear coefficient units/material traceability verified; numerical convergence separately documented.
- **validation method:** Blind instrumented response comparison; prospective inspected cohort; flow/material wear programme; independent domain review.
- **relative effort:** XL
- **sources:** S10
- **depends on:** GD-A05,GD-A07

## GD-A16 — Field anomaly replay evaluation

- **priority:** P2
- **capability:** Field anomaly replay evaluation
- **user problem:** Synthetic event results cannot establish detection performance.
- **proposed solution:** Adjudicated multisensor field corpus, operator context, prospective shadow evaluation and workload analysis.
- **expected value or hypothesis:** Quantifies false candidates, misses and latency before product claims.
- **dependencies and data:** GD-A05/A07/A09; ethical authorized corpus.
- **engineering or data risks:** Leakage, ambiguous labels, missed serious events.
- **acceptance criteria:** Only causal available inputs used; thresholds frozen before holdout; sensitivity/missed events/false candidates per monitored hour and latency distributions with uncertainty disclosed; transfer/pump/trip contexts stratified; display remains advisory.
- **validation method:** Independent adjudication; held-out wells with baseline timing; prefix invariance; authorized passive shadow study after separate approval.
- **relative effort:** XL
- **sources:** S10,S12
- **depends on:** GD-A05,GD-A07,GD-A09

## GD-A17 — Actual-fluid thermodynamics and geomechanics

- **priority:** P2
- **capability:** Actual-fluid thermodynamics and geomechanics
- **user problem:** Reduced models exclude actual mud and formation coupling.
- **proposed solution:** External characterized PVT/solubility adapter and selected thermal/poroelastic or multiphase solver experiments.
- **expected value or hypothesis:** Extends M7/M16 for independently defined questions.
- **dependencies and data:** GD-A05/A11; measured fluid/property data and solver rights.
- **engineering or data risks:** Uncharacterized mud, nonunique stress inputs, EOS stability.
- **acceptance criteria:** No binary EOS relabelled actual mud; composition/T/P validity explicit; mass/energy/material balances and phase stability checked; withheld beyond measured range; independent PVT and geomechanics cases required.
- **validation method:** Laboratory blind comparisons; documented solver verification and mesh/time sensitivity; geomechanical reviewer.
- **relative effort:** XL
- **sources:** Local model specifications
- **depends on:** GD-A05,GD-A11

## GD-A18 — Evidence search assistant

- **priority:** P2
- **capability:** Evidence search assistant
- **user problem:** Engineers may struggle to locate relevant reports and assumptions.
- **proposed solution:** Permission-aware retrieval over project evidence with file/page citations, calculations delegated to typed kernels.
- **expected value or hypothesis:** Faster evidence lookup; hypothesis H9.
- **dependencies and data:** GD-A01/A03/A09; evaluation questions and document rights.
- **engineering or data risks:** Hallucinated citations, prompt injection, hidden unit errors.
- **acceptance criteria:** Every factual answer links exact source/page; missing evidence abstains; conflicting versions exposed; no writes or control authority; calculated results include model/version/inputs; unauthorized sources inaccessible.
- **validation method:** Fixed answerable/unanswerable/conflicting question set; citation correctness and abstention scored; adversarial documents; compare task time to manual search.
- **relative effort:** M
- **sources:** S16
- **depends on:** GD-A01,GD-A03,GD-A09

## GD-A19 — Autonomous rig control

- **priority:** Excluded
- **capability:** Autonomous rig control
- **user problem:** Original proposal exceeded the audited authority boundary.
- **proposed solution:** Preserve simulator-only Module 17 and equipment_control false.
- **expected value or hypothesis:** Maintains declared scope.
- **dependencies and data:** Separate future OEM governance would require new authorization; not part of this backlog.
- **engineering or data risks:** Unauthorized authority expansion.
- **acceptance criteria:** No hardware adapters, outbound equipment commands or rig leases introduced; simulation requests remain isolated.
- **validation method:** Regression route inventory and no-authority/fault tests; preserve release boundary.
- **relative effort:** Not estimated
- **sources:** Local audit and M17 specification
- **depends on:** None

