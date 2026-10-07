# Wellbore revision ownership — v0.9 continuation

Verified starting application/documentation checkout: `67ca21d93ce2aef5c40abb3c065c4d29bebda47b`; clean before changes. The handoff's 15 audit tests were independently rerun and passed. Public Streamlit and research-6 remain the previous alpha until a later verified release.

This increment implements architecture phases 3–4: project → well → wellbore → planned/actual/scenario survey revision → authoritative saved trajectory/geometry → uncertainty/proximity → fixed report. It retains existing project-scoped sources and immutable geometry/calculations/reports without inventing wellbore ownership.

## Acceptance gates

- [x] Additive, atomic schema migration; existing records and original bytes remain unchanged.
- [x] Immutable survey, trajectory and calculation records with wellbore/type ownership, hashes, audit actor and source references.
- [x] Optimistic revision conflicts are independent for each wellbore and planned/actual/scenario lane.
- [x] Original CSV import and authored SI station edits; explicit coordinate frame, datum, north, origins and evidence state.
- [x] Explicit adoption of an existing project source; no automatic assignment or fabricated reference metadata.
- [x] Wellbore selection drives survey/trajectory/header/shared MD/spatial view and scoped geometry editing.
- [x] Planned/actual comparison and offset selection use saved canonical coordinates and distinguish their data roles.
- [x] Uncertainty and proximity call preserved kernels, bind exact source revisions, persist withholding and forbid clearance.
- [x] Staleness covers subject and offset dependencies; reopening a historical revision never activates it silently.
- [x] New fixed reports include hierarchy, immutable revisions and dependency state; prior report bytes remain unchanged.
- [x] Project export/fresh restore and whole-workstation backup retain hierarchy and revision ownership; old bundles still open.
- [x] Team membership, cross-project/cross-wellbore references, source tampering and stale saves are tested.
- [x] Focused regression, complete suite (697 passed), TypeScript/build, rendered authored edit, explicit adoption, reopen, fixed report and restart checks pass. Original CSV bytes are covered by API integration tests; the Chrome chooser remains blocked by its existing file-access permission.

## Persistence and compatibility

Use an append-only wellbore revision table with independent revision numbers per wellbore, record kind and trajectory role. Current heads are derived from the newest committed record, rather than changing immutable historical records. A saved trajectory also supplies the existing M1 geometry representation in the same database transaction so existing engineering kernels and evidence routes remain authoritative.

Survey inputs preserve original sources in the existing raw/Parquet store. Datum and north reference must match the project. Explicit shared-frame origins are required for offset comparison; unsupported frame conversions are withheld, not inferred. Authored plan data and imported actual observations remain unqualified sources.

Staleness is derived from revision references and current heads. Preserve original calculated/withheld status and display freshness separately. Reports freeze that dependency state; their integrity hash does not change when later data arrive.

Extend project bundles with versioned hierarchy/revision entries and strict ownership validation. Restore must preserve IDs/hashes and reject collisions/foreign parents atomically. The complete wellbore snapshot is separate from legacy project-scoped records.

## Boundaries

No engineering equation, model version, unit convention, north convention, applicability or threshold changes. No independent field qualification, publisher trust, automated clearance or equipment authority. Three.js/docking/Tauri/enterprise infrastructure remain separate architecture gates after this connected increment.

## Verified candidate and remaining release checks

Candidate version: **0.9.0-alpha.2** on `v09-wellbore-revisions`. The complete local suite passed 697 tests with no failures or skips and one upstream Starlette/httpx deprecation warning. Fourteen new tests cover ownership, independent lanes, conflicting writers, original CSV bytes, cross-project and team access, semantic archive tampering, reports, restart and workstation recovery. Local source browser checks cover planned/actual comparison, shared MD, saved casing geometry, scoped torque/drag, offset staleness, historical inspection and original fixed-report download. Streamlit transport integration is tested independently. Public main, hosted Streamlit and research-6 remain alpha.1 until a subsequent approved publication.

The new proximity wrapper rejects correlated-error modes because the preserved distance kernel does not implement them. Covariance separation factors and drilling clearance are withheld. Offset comparisons require an explicitly shared frame and are bounded to 100,000 segment pairs; no automatic resampling is performed. Grid-north uncertainty requires an explicit supported conversion rather than an inferred one. The spatial viewer remains the disclosed SVG interim viewer.
