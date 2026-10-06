# GeoDrill Pro v0.9 — Implementation Master Prompt

## Purpose

Use this prompt to continue building **GeoDrill Pro v0.9** from the existing GeoDrill Pro repository and the approved architecture specification.

This is not a greenfield rewrite.

The implementation must:

1. preserve existing verified engineering logic;
2. preserve existing provenance, evidence, recovery, security, and test infrastructure;
3. refactor the application toward the v0.9 workstation architecture;
4. implement the new professional drilling-engineering UX;
5. introduce the new GeoDrill branding and feature-symbol system;
6. introduce the 2D/3D engineering workspace architecture;
7. prepare the platform for WITSML/ETP realtime ingestion;
8. remove the old user-facing “17 modules” framing;
9. maintain strict engineering traceability and qualification boundaries;
10. leave a complete progress record whenever the session must stop.

---

# 1. Authoritative Inputs

Before modifying code, read and use these sources as the implementation basis.

## Primary architecture specification

`GEODRILL_PRO_V0.9_FULL_STACK_ARCHITECTURE.md`

Treat this file as the primary product and technical architecture specification.

Do not silently replace its architecture with a different design unless a concrete technical incompatibility is demonstrated.

## Existing repository

Primary repository:

`https://github.com/Nabilvisi/geodrill-pro`

If a connected Project Drill / OneDrive working copy is available, inspect that copy as well.

The existing application already contains validated or partially validated work and must not be discarded without evidence.

## Existing release baseline

Preserve the most recent verified baseline before beginning structural changes.

At the time this implementation prompt was written, the product direction was:

```text
v0.8
Engineering research foundation

        ↓

v0.9
Integrated drilling engineering workstation

        ↓

v1.0 target
Qualified, polished production platform
```

---

# 2. Product Definition

Build GeoDrill Pro as:

> **An integrated drilling engineering workstation for planning, designing, analysing, visualizing, monitoring, and reviewing wells from pre-drill planning through execution and post-well analysis.**

The main workflow is:

```text
Project / Field
      ↓
Well / Wellbore
      ↓
Well Planning
      ↓
Directional Design
      ↓
Survey Management
      ↓
Anti-Collision / Uncertainty
      ↓
3D Well Engineering Model
      ↓
Drilling Engineering Calculations
      ↓
Realtime / Execution Monitoring
      ↓
Post-Well / Offset Analytics
      ↓
Evidence / Reports / Review
```

Do not turn GeoDrill Pro into a general oil-and-gas application.

Primary users are:

- Drilling Engineers
- Directional Drillers
- MWD Engineers
- LWD Engineers
- Well Planning Engineers
- Drilling Optimization Engineers
- Drilling Supervisors
- Wellsite Engineers

---

# 3. Product Scope

## Core identity

Highest priority:

- Projects
- Fields
- Wells
- Wellbores
- Well Planning
- Directional Engineering
- Survey Management
- Anti-Collision
- ISCWSA-style uncertainty workflows
- Offset wells
- Planned versus actual trajectories
- 2D planning
- Section views
- 3D well visualization

## Drilling engineering

Integrate:

- Hydraulics
- ECD / pressure
- Rheology
- Torque & Drag
- Buckling
- Casing
- BHA
- Hole Cleaning
- Surge & Swab
- Mechanical Specific Energy
- Geomechanics
- Wellbore Stability
- Dynamics / Vibration

## Operations

Build toward:

- WITSML
- ETP
- replay
- realtime monitoring
- source/arrival timestamps
- channel quality
- derived channels
- plan versus actual
- event review

Realtime must remain **read-only** unless a future explicitly qualified scope authorizes something else.

## Analytics

Support:

- Offset benchmarking
- drilling performance analytics
- anomaly analysis
- research ML models
- post-well review

## Enterprise

Prepare for:

- users
- teams
- RBAC
- review
- approval
- audit
- cloud
- on-prem
- project isolation
- release signing
- recovery

---

# 4. Explicit Non-Goals

Do not claim or implement as operational authority in v0.9:

- autonomous rig control;
- automatic well control;
- automated drilling clearance;
- guaranteed kick detection;
- guaranteed loss detection;
- automatic mud-weight approval;
- automatic casing/barrier approval;
- unqualified operating recommendations;
- SCADA replacement;
- seismic interpretation suite;
- reservoir simulator;
- full Petrel replacement.

The application can display or analyse such supporting data where it is relevant to drilling.

---

# 5. Critical Migration Rule

## Do not rebuild from zero.

The implementation strategy is:

```text
CURRENT GEODRILL
       │
       ├── preserve engineering kernels
       ├── preserve tests
       ├── preserve provenance
       ├── preserve evidence
       ├── preserve backup / restore
       └── preserve verified behavior
                │
                ▼
        ARCHITECTURAL REFACTOR
                │
                ├── domain model
                ├── application services
                ├── modular API
                ├── design system
                ├── workstation shell
                ├── 2D / 3D engine
                └── realtime foundation
```

Existing behavior may only be deleted when:

1. its replacement exists;
2. regression tests pass;
3. saved project compatibility has been considered;
4. migration is documented.

---

# 6. Preserve These Existing Assets

Unless code inspection proves otherwise, preserve and evolve:

- `packages/engineering`
- directional calculations
- minimum-curvature implementation
- geodesy
- coordinate transformation
- uncertainty work
- proximity / anti-collision work
- hydraulics
- torque & drag
- buckling
- casing calculations
- geomechanics
- MSE
- offset analytics
- evidence / provenance
- report generation
- audit history
- FastAPI
- React
- TypeScript
- Vite
- Python
- Pydantic
- `pyproj`
- existing use of `welleng`
- SQLite
- DuckDB
- Parquet
- pytest
- Hypothesis
- GitHub Actions
- Windows packaging
- backup / recovery
- source hashes
- saved-study behavior
- qualification / withholding concepts

---

# 7. Remove the Old Product Framing

The user-facing application must not present itself as:

- “17 modules”
- “Modules 1–17”
- “M1–M17” as the primary navigation model

Internal migration references may temporarily remain where needed for backwards compatibility and engineering traceability.

The new user-facing navigation must use drilling workflows.

Recommended navigation:

```text
PROJECTS
  Projects

PLAN & DESIGN
  Well Planning
  Directional
  Survey
  Anti-Collision
  3D Well Model

ENGINEERING
  Hydraulics
  Torque & Drag
  Casing
  BHA
  Geomechanics

OPERATIONS
  Realtime
  Offsets

GOVERNANCE
  Evidence
  Reports
  Qualification
  Admin
```

---

# 8. GeoDrill Branding

Apply the approved GeoDrill Pro v0.9 design direction.

Brand concept:

- letter **G**
- directional trajectory
- drilling target
- subsurface layers
- drilling / rig context

Primary colors:

```text
Deep Blue      #0B3D91
Teal           #0EA5B7
Graphite       #374151
Stone          #94A3B8
Orange         #F97316
Success        #10B981
Warning        #F59E0B
Danger         #EF4444
Info           #3B82F6
Background     #F8FAFC
Surface        #FFFFFF
Border         #E2E8F0
Text           #0F172A
```

Add original GeoDrill feature icons for:

```text
Projects
Well Planning
Directional
Survey
Anti-Collision
3D Well Model
Hydraulics
Torque & Drag
Casing
BHA
Geomechanics
Realtime
Offsets
Evidence
Reports
Qualification
Admin
```

Do not copy commercial vendor logos or proprietary trade dress.

---

# 9. Target Architecture

Move toward:

```text
geodrill-pro/
│
├── apps/
│   ├── web/
│   ├── desktop/
│   └── streamlit/
│
├── services/
│   ├── api/
│   ├── application/
│   ├── realtime/
│   ├── workers/
│   └── integrations/
│
├── packages/
│   ├── domain/
│   ├── engineering/
│   ├── research/
│   ├── contracts/
│   └── streaming/
│
├── qualification/
├── tests/
├── docs/
└── tools/
```

Do not mechanically move files just to match this tree.

Refactor only when responsibilities are clear and tests remain valid.

---

# 10. Frontend Direction

Retain:

- React
- TypeScript
- Vite

Preferred additions:

- TanStack Router
- TanStack Query
- Zustand
- React Hook Form
- Zod
- Web Workers where justified

Do not put all state into one global store.

Separate:

```text
Server state
Workstation state
Form state
Realtime state
3D scene state
```

---

# 11. Workstation UI

The primary product must become a professional engineering workstation.

Target layout:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ GeoDrill Pro | Project / Well / Revision | Search | Sync | User       │
├────────────┬──────────────────────────────────────────┬─────────────────┤
│ Navigation │                                          │ Inspector       │
│            │              Main Workspace              │                 │
│ Project    │                                          │ Selection       │
│ Planning   │       2D / 3D / plots / tables          │ Parameters      │
│ Direction  │                                          │ Evidence        │
│ Survey     │                                          │ Limits          │
│ Collision  │                                          │ Qualification   │
├────────────┴──────────────────────────────────────────┴─────────────────┤
│ Events | validation | model | units | CRS | calculation status        │
└────────────────────────────────────────────────────────────────────────┘
```

Support:

- resizable panels;
- dockable panels;
- persistent layouts;
- compact engineering density;
- keyboard shortcuts;
- command palette;
- synchronized selections.

---

# 12. Data Grid

Use a serious engineering grid.

Requirements:

- virtualization;
- editable cells;
- pinned columns;
- units;
- validation;
- grouping;
- filtering;
- copy/paste;
- keyboard navigation;
- export;
- provenance;
- conditional formatting;
- precision handling.

Preferred options:

- AG Grid when licensing is acceptable;
- otherwise TanStack Table + TanStack Virtual.

---

# 13. Plotting

Recommended:

- Apache ECharts for engineering plots;
- uPlot for high-frequency realtime plots;
- Plotly only where it provides clear value.

Build one central cursor/selection coordinator.

Example:

```text
Select MD 2510 m in survey grid

        ↓

2D plan
Section view
3D model
Hydraulics plot
Torque/drag plot
Survey plots

all move to the same engineering location
```

---

# 14. 3D Engineering System

Use:

- Three.js
- React Three Fiber
- Drei

Optional:

- CesiumJS for field-scale/global geospatial views
- MapLibre / deck.gl for map workflows

The engineering kernel remains authoritative.

Correct:

```text
Survey Inputs
     ↓
Directional Kernel
     ↓
Canonical Engineering Coordinates
     ↓
3D Scene
```

Do not calculate authoritative trajectory geometry independently in Three.js.

3D must support:

- planned trajectory;
- actual trajectory;
- offset wells;
- survey stations;
- targets;
- formation surfaces;
- faults;
- casing;
- hole sections;
- BHA;
- uncertainty ellipsoids;
- closest approach;
- anti-collision indicators;
- labels;
- clipping;
- measurements;
- object picking;
- visibility layers.

Every 3D scene must know:

- CRS;
- datum;
- north reference;
- grid convergence where relevant;
- elevation reference;
- local origin;
- units.

---

# 15. Backend Refactor

Retain FastAPI.

Move routing toward:

```text
services/api/routers/
├── projects.py
├── wells.py
├── trajectories.py
├── surveys.py
├── anticollision.py
├── hydraulics.py
├── torque_drag.py
├── casing.py
├── geomechanics.py
├── realtime.py
├── offsets.py
├── evidence.py
├── reports.py
├── qualification.py
└── admin.py
```

API routers must not contain engineering equations.

Use:

```text
HTTP Router
    ↓
Application Service
    ↓
Domain Model
    ↓
Engineering Kernel / Repository
```

---

# 16. Engineering Kernel Rules

Separate engineering logic into:

```text
A. Deterministic / Verified
B. Deterministic / Research
C. Statistical / ML
D. Operational Decision Support
```

Every calculation must return a standard envelope.

Minimum fields:

```text
calculation_id
model
model_version
qualification
status
inputs_hash
geometry_revision_id
result
assumptions
warnings
limitations
evidence_ids
created_at
software_revision
```

Calculation status:

```text
calculated
withheld
invalid
failed
stale
superseded
not_applicable
```

---

# 17. Units

Canonical rule:

```text
External units
      ↓
Boundary conversion
      ↓
SI
      ↓
Engineering kernel
      ↓
SI result
      ↓
Display conversion
```

Never silently infer units.

Never allow a display unit to become the kernel authority.

---

# 18. Core Domain Model

Build around:

```text
Organization
└── Project
    ├── Field
    └── Well
        └── Wellbore
            ├── TrajectoryRevision
            ├── SurveyRevision
            ├── Targets
            ├── Formations
            ├── HoleSections
            ├── CasingProgramme
            ├── BHAProgramme
            ├── MudProgramme
            ├── EngineeringCases
            └── RealtimeRuns
```

Every calculation must bind to the relevant source revisions.

---

# 19. Calculation Staleness

Implement a dependency graph.

Example:

```text
Trajectory changed
      │
      ├── Anti-Collision  → STALE
      ├── Torque & Drag   → STALE
      ├── Hydraulics      → STALE
      ├── Casing          → STALE
      ├── Geomechanics    → STALE
      └── Reports         → STALE
```

A stale result must never appear current without a visible status.

---

# 20. Local Persistence

Retain:

```text
SQLite
DuckDB
Parquet
Raw immutable source files
```

Responsibilities:

```text
SQLite    metadata / transactions / project state
DuckDB    analytics
Parquet   normalized datasets / time series snapshots
Raw       original source bytes
```

---

# 21. Enterprise Persistence Target

Prepare abstractions for:

```text
PostgreSQL
PostGIS
TimescaleDB
S3 / MinIO
Redis optional
NATS optional
```

Do not introduce infrastructure without a justified requirement.

Local mode must remain simple.

---

# 22. Realtime

Build a read-only realtime architecture:

```text
Rig / EDR
      ↓
WITSML / ETP
      ↓
Connector
      ↓
Raw Capture
      ↓
Normalization
      ↓
Quality
      ↓
Canonical Channels
      ↓
Derived Channels
      ↓
Store
      ↓
WebSocket
      ↓
GeoDrill Realtime Workspace
```

Preserve:

- raw payload;
- source timestamp;
- arrival timestamp;
- sequence;
- mapping;
- units;
- quality;
- source system.

Quality states:

```text
valid
missing
stale
duplicate
out_of_order
out_of_range
unit_unknown
mapping_unknown
quarantined
```

---

# 23. Replay

Replay must support:

- source time;
- arrival time;
- seek;
- pause;
- speed;
- gap preservation;
- deterministic fixtures;
- historical runs.

Use the same canonical pipeline for replay and live data whenever practical.

---

# 24. Evidence and Provenance

Do not weaken the current evidence model.

Every imported source should retain:

```text
filename
raw hash
raw bytes or immutable object reference
source
importer version
mapping
units
accepted rows
rejected rows
warnings
timestamp
```

Every engineering result should be traceable to:

```text
source data
input revision
model
model version
software revision
calculation record
evidence record
report
```

---

# 25. Security

Maintain or add:

- strict local network binding where local-only;
- TLS for server deployment;
- OIDC for enterprise;
- RBAC;
- encrypted secrets;
- signed releases;
- SBOM;
- dependency scanning;
- SAST;
- secure XML;
- archive traversal protection;
- file size limits;
- upload validation;
- audit;
- backup verification;
- secure restore;
- least privilege.

Never commit:

- private signing keys;
- passwords;
- production tokens;
- certificates containing private keys.

---

# 26. RBAC

Target roles:

```text
Viewer
Engineer
Author
Reviewer
Approver
Project Admin
Organization Admin
```

Support four-eyes review where configured.

---

# 27. Desktop

Tauri 2 is the preferred future desktop shell.

Target:

```text
Tauri
├── React
├── FastAPI sidecar
├── engineering kernels
├── local data
└── updater/signing
```

Do not block early v0.9 work on Tauri.

First stabilize:

- API;
- domain model;
- React workstation.

---

# 28. Streamlit

Keep Streamlit as:

- research demo;
- public preview;
- lightweight cloud demonstration;
- stakeholder review surface.

Do not use Streamlit as the main v0.9 workstation architecture.

---

# 29. Qualification

Always distinguish:

```text
IMPLEMENTED
VERIFIED
BENCHMARKED
INDEPENDENTLY QUALIFIED
```

Never call a model qualified merely because tests pass.

Every model should expose a qualification state.

---

# 30. Testing Requirements

Maintain and expand:

## Python

- pytest
- Hypothesis

## Frontend

- Vitest
- React Testing Library

## Browser

- Playwright

## Required test categories

```text
unit
property
contract
integration
end-to-end
qualification
visual
release
```

Critical end-to-end workflow:

```text
Create project
      ↓
Create well
      ↓
Import survey
      ↓
Accept survey
      ↓
Create plan
      ↓
Open 3D
      ↓
Run anti-collision
      ↓
Run engineering case
      ↓
Save
      ↓
Reopen
      ↓
Generate report
      ↓
Backup
      ↓
Restore
```

---

# 31. Implementation Order

Follow this order unless repository inspection identifies a blocking dependency.

## Phase 0 — Baseline

- verify current branch;
- verify current tests;
- record current release;
- create safe implementation branch;
- create initial progress file.

## Phase 1 — Architecture foundation

- domain package;
- application services;
- modular routers;
- calculation envelope;
- standard errors;
- dependency / stale graph.

## Phase 2 — Design system

- branding;
- feature icons;
- tokens;
- sidebar;
- top bar;
- themes;
- application shell;
- dock system.

## Phase 3 — Project / Well hierarchy

- project;
- field;
- well;
- wellbore;
- revision;
- target;
- project tree.

## Phase 4 — Directional flagship

- plan editor;
- survey grid;
- trajectory;
- uncertainty;
- anti-collision;
- synchronized plots.

## Phase 5 — 3D

- R3F / Three.js;
- trajectory;
- actual;
- offsets;
- targets;
- formations;
- uncertainty;
- casing;
- BHA.

## Phase 6 — Engineering workspaces

- hydraulics;
- torque & drag;
- casing;
- BHA;
- geomechanics;
- performance.

## Phase 7 — Realtime

- canonical channel model;
- replay;
- quality;
- WebSocket;
- WITSML;
- ETP.

## Phase 8 — Desktop

- Tauri;
- sidecar;
- signing;
- update / rollback.

## Phase 9 — Enterprise

- PostgreSQL;
- PostGIS;
- Timescale;
- object storage;
- OIDC;
- RBAC.

## Phase 10 — Qualification

- benchmark datasets;
- independent review;
- field evidence.

---

# 32. Work Style

Do not attempt to implement all of v0.9 in one unstructured change.

Work incrementally.

For each increment:

1. inspect current code;
2. identify dependencies;
3. define acceptance criteria;
4. implement;
5. run focused tests;
6. run regression;
7. inspect changed files;
8. document what changed;
9. commit only coherent increments where repository access allows;
10. update the progress record.

Prefer working software over speculative scaffolding.

Do not add dependencies simply because they appear in this prompt.

A dependency must solve a current architectural need.

---

# 33. Mandatory Progress Recording

Create and maintain:

`GEODRILL_PRO_V0.9_PROGRESS.md`

at the repository root or another clearly documented project location.

Update it at meaningful checkpoints.

The progress file is the authoritative session-to-session handoff.

Do not rely only on chat history.

---

# 34. Five-Hour Limit Safety Protocol

## Important limitation

Do not claim to know the user's ChatGPT UI usage meter unless the environment explicitly exposes it.

If the environment, tool, system message, or user provides a value for **Five Hour Limit Remaining**, use that value.

### Mandatory threshold

If the available Five Hour Limit Remaining is **10% or lower**, immediately stop starting new implementation work.

Do not begin:

- a refactor;
- a dependency migration;
- a large test run;
- a deployment;
- a new feature;
- a broad file rewrite.

Instead perform only safe shutdown / handoff actions.

### Safe shutdown sequence

When remaining allowance reaches or falls below 10%:

1. finish only the smallest currently active atomic edit if abandoning it would corrupt the repository;
2. do not start another implementation task;
3. run only essential targeted validation if it is short enough to establish repository state;
4. record the exact repository status;
5. update `GEODRILL_PRO_V0.9_PROGRESS.md`;
6. include incomplete work explicitly;
7. record failing tests;
8. record modified/untracked files;
9. record the current branch and latest commit;
10. record the next exact command or task for continuation;
11. end the session after the handoff is saved.

### If remaining percentage is not visible

Because the model may not have direct access to the UI usage meter:

- never invent the percentage;
- checkpoint progress frequently anyway;
- update the progress file after every major milestone;
- update it before high-risk or long-running work;
- if the user says the remaining allowance is near 10%, trigger the shutdown protocol immediately.

### Conservative checkpoint rule

Even without meter access, update the progress file:

- after each completed implementation phase;
- after each major refactor;
- after each successful migration;
- after every meaningful Git commit;
- after resolving a major failure;
- before switching subsystems;
- before deployment/release activity;
- before lengthy test suites when substantial work has accumulated.

This ensures that a sudden session end does not lose implementation context.

---

# 35. Mandatory Progress File Format

Use exactly this high-level structure.

```markdown
# GeoDrill Pro v0.9 — Implementation Progress

## Session Metadata

- Date:
- Session:
- Repository:
- Branch:
- HEAD commit:
- Working tree:
- Five Hour Limit Remaining:
- Reason session stopped:

## Current Objective

Describe the exact objective that was being implemented.

## Architecture Phase

Current phase from the v0.9 roadmap.

## Completed This Session

- item
- item
- item

## Files Added

| File | Purpose |
|---|---|

## Files Modified

| File | Change |
|---|---|

## Files Deleted / Retired

| File | Reason |
|---|---|

## Architecture Decisions

### Decision
Reason.

## Dependencies Added / Removed

| Dependency | Change | Reason |
|---|---|---|

## Database / Schema Changes

Describe migrations and compatibility implications.

## API Changes

List new, changed, deprecated, or removed endpoints.

## Engineering Kernel Changes

For each change record:

- model;
- model version;
- equations affected;
- units;
- applicability;
- qualification impact;
- regression evidence.

## UI / UX Changes

Record:

- navigation;
- pages;
- components;
- design tokens;
- icons;
- 2D/3D behavior.

## Branding Changes

Record:

- logos;
- icons;
- asset paths;
- design-token updates.

## 3D Changes

Record:

- scene entities;
- coordinate handling;
- picking;
- performance;
- known defects.

## Realtime Changes

Record:

- connector;
- channel mapping;
- source time;
- arrival time;
- quality;
- replay.

## Tests Run

| Command | Result | Notes |
|---|---|---|

## Test Summary

- Passed:
- Failed:
- Skipped:
- Known failures:

## Manual Verification

Document manual checks performed.

## Current Working Tree

Include `git status --short` or equivalent.

## Known Issues

### Issue
- Severity:
- Description:
- Reproduction:
- Workaround:
- Next action:

## Incomplete Work

Record every partially implemented task.

## Important Do Not Break Items

List critical invariants discovered during the session.

## Next Session — Start Here

### First task

Exact next implementation task.

### First files to inspect

- file
- file

### First commands to run

```bash
...
```

## Next 3 Priorities

1.
2.
3.

## Acceptance Criteria Still Open

- [ ] item
- [ ] item

## Deferred Work

List intentionally deferred work.

## Source / Evidence Notes

Record source documents, benchmark datasets, hashes, or engineering references relevant to continuation.

## Handoff Summary

A concise paragraph explaining the repository state and how the next session should continue.
```

---

# 36. Continuation Protocol for a New Session

At the beginning of every new implementation session:

1. read `GEODRILL_PRO_V0.9_FULL_STACK_ARCHITECTURE.md`;
2. read `GEODRILL_PRO_V0.9_PROGRESS.md`;
3. inspect Git status;
4. inspect current branch and HEAD;
5. read files listed under **Next Session — Start Here**;
6. run the minimum baseline tests listed in the handoff;
7. verify that the handoff still matches repository state;
8. continue the first unfinished acceptance criterion.

Do not restart planning from zero unless the progress file explicitly says the architecture changed.

---

# 37. Git Safety

Before major changes:

```bash
git status
git branch --show-current
git rev-parse HEAD
```

Do not discard local changes that were not created by the current session.

Do not:

```text
git reset --hard
git clean -fd
force push
delete branches
rewrite history
```

unless explicitly authorized and clearly justified.

Prefer coherent commits.

Suggested commit examples:

```text
feat(workstation): add GeoDrill v0.9 app shell
refactor(api): split directional routes from main service
feat(3d): add synchronized trajectory scene
feat(domain): introduce wellbore revision model
feat(realtime): add canonical channel quality model
test(directional): add workstation regression coverage
docs(progress): checkpoint v0.9 implementation state
```

---

# 38. Engineering Safety Rules

Never silently:

- alter a validated equation;
- change unit conventions;
- change coordinate conventions;
- change north reference;
- change datum behavior;
- change uncertainty assumptions;
- change thresholds;
- change a model's declared applicability.

If an engineering kernel changes:

1. document the reason;
2. update model version if behavior changes;
3. add regression tests;
4. compare previous results;
5. record the change in progress;
6. update the applicable model specification.

---

# 39. Quality Gate Before Calling an Increment Complete

An increment is complete only if:

- code is implemented;
- tests pass for its intended scope;
- migration impact is understood;
- UI is connected where required;
- evidence/provenance remains intact;
- error behavior is intentional;
- limitations are visible;
- progress file is updated.

Do not call a kernel/API-only capability a completed product workflow if the UI/integration acceptance criterion is still open.

---

# 40. Definition of Success

GeoDrill Pro v0.9 succeeds when:

1. users navigate by real drilling workflows rather than numbered modules;
2. the engineering kernel remains authoritative;
3. project, well, and wellbore context is explicit;
4. selected engineering entities synchronize across tables, plots, 2D, and 3D;
5. 3D geometry matches engineering coordinates;
6. every result is tied to source revisions and model versions;
7. stale results cannot masquerade as current;
8. planned, actual, historical, research, and qualified information are visually distinct;
9. realtime data is quality-aware and traceable;
10. the application has original GeoDrill branding and symbols;
11. existing verified work survives the transition;
12. every interrupted session can be continued from the progress MD without reconstructing context from memory.

---

# 41. First Action When This Prompt Is Used

Do not immediately modify code.

First:

1. locate the repository;
2. read the v0.9 architecture MD;
3. read the existing progress MD if present;
4. inspect branch / HEAD / working tree;
5. inspect current tests and build scripts;
6. inspect the current frontend, API, and engineering packages;
7. determine the current roadmap phase;
8. create/update `GEODRILL_PRO_V0.9_PROGRESS.md`;
9. identify one coherent implementation increment;
10. execute that increment completely before starting another.

Then continue incrementally until:

- the requested scope is complete; or
- an external blocker requires user action; or
- the Five Hour Limit Remaining reaches the mandatory stop threshold.

---

# 42. Final Session Rule

Never end a substantial GeoDrill implementation session with only a conversational summary.

Before ending, ensure the repository contains an updated:

`GEODRILL_PRO_V0.9_PROGRESS.md`

that is detailed enough for a fresh session with no chat history to resume the work correctly.

The progress file is part of the implementation deliverable.
