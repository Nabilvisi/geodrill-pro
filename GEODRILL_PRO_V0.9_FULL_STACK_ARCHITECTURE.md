# GeoDrill Pro v0.9
## Full-Stack Product, Software, Engineering, 3D, Realtime, UI/UX, Security, and Qualification Architecture

**Document type:** Product + Technical Architecture Specification  
**Target release:** GeoDrill Pro v0.9  
**Product class:** Drilling Engineering Workstation  
**Primary users:** Drilling Engineers, Directional Drillers, MWD/LWD Engineers, Well Planning Engineers, Drilling Optimization Engineers, Drilling Supervisors, Wellsite Engineers  
**Status:** Architecture baseline for implementation  
**Supersedes:** The user-facing concept of a fixed “17 module” product  
**Core principle:** Preserve verified engineering work; refactor the platform around it; add a professional workstation, 3D, realtime, enterprise, and qualification layers.

---

# 1. Executive Summary

GeoDrill Pro v0.9 should not be a clean-sheet rewrite of v0.8. The existing product already contains valuable engineering kernels, test coverage, provenance mechanisms, recovery logic, API functionality, research workflows, and release verification. The correct strategy is an **evolutionary platform refactor**.

The v0.9 goal is to transform GeoDrill Pro from an engineering research application into a coherent **drilling engineering workstation** with the following end-to-end product workflow:

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
Execution / Realtime Monitoring
    ↓
Post-Well / Offset Analytics
    ↓
Evidence / Reports / Review
```

The application should be positioned as:

> **GeoDrill Pro is an integrated drilling engineering workstation for planning, designing, analysing, visualizing, monitoring, and reviewing wells from pre-drill planning through execution and post-well analysis.**

The product should not be positioned as a Petrel replacement, reservoir simulator, geological interpretation suite, SCADA system, rig control platform, or autonomous drilling controller.

The user-facing application must no longer expose the old framing of “17 modules.” Capabilities must instead be grouped by real drilling workflows and engineering workspaces.

---

# 2. Product Direction

## 2.1 Primary product identity

GeoDrill Pro v0.9 is built around five product pillars:

1. **Well Planning & Directional Engineering**
2. **Drilling Engineering**
3. **3D Well Engineering**
4. **Realtime Drilling Operations**
5. **Engineering Evidence & Post-Well Analytics**

These pillars should drive the information architecture, navigation, API boundaries, data model, testing strategy, and release roadmap.

## 2.2 Product priorities

### Tier 1 — Core identity

- Projects / Fields / Wells / Wellbores
- Well planning
- Directional planning
- Survey management
- Minimum curvature
- DLS / TVD / North / East
- Coordinate reference systems
- Targets
- Planned vs actual trajectory
- Survey uncertainty
- ISCWSA-style error-model support
- Anti-collision
- Closest approach
- Separation factor
- Offset wells
- 2D + 3D well visualization

### Tier 2 — Drilling engineering

- Hydraulics
- ECD / pressure profiles
- Rheology
- Torque & drag
- Buckling
- Casing design
- BHA representation
- Hole cleaning
- Surge & swab
- MSE / drilling performance
- Geomechanics
- Wellbore stability
- Dynamics / vibration

### Tier 3 — Operations

- WITSML / ETP read-only ingestion
- Rig / EDR channel mapping
- Realtime channel visualization
- Plan vs actual
- Telemetry quality
- Event monitoring
- Data replay
- Derived channels
- MSE trend
- operational-context dashboards

### Tier 4 — Intelligence

- Offset analytics
- NPT / event benchmarking
- anomaly detection
- clustering
- drilling performance analytics
- ML-assisted interpretation
- recommendation support with explicit limitations

### Tier 5 — Enterprise

- users / teams
- RBAC
- approvals
- project permissions
- audit history
- signed evidence
- cloud / on-prem deployment
- backup / restore
- release signing
- security review
- organization-level governance

---

# 3. Explicit Non-Goals for v0.9

GeoDrill Pro v0.9 must not claim to provide:

- automated rig control;
- autonomous well control;
- automated drilling clearance;
- guaranteed kick/loss detection;
- automatic operational approval;
- certified casing/barrier compliance without qualified evidence;
- full seismic interpretation;
- full reservoir simulation;
- full geological modelling;
- SCADA replacement;
- ERP / finance / supply chain functions.

GeoDrill may consume subsurface information when it supports drilling, including:

- formation tops;
- target windows;
- pore pressure;
- fracture gradient;
- lithology;
- faults;
- reservoir targets;
- seismic-derived surfaces;
- offset-well geometry.

---

# 4. v0.8 → v0.9 Migration Strategy

## 4.1 Do not rewrite the engineering core

The highest-value current assets should be preserved:

| Current capability | v0.9 action |
|---|---|
| `packages/engineering` | Preserve and reorganize by domain |
| Directional calculation logic | Preserve, deepen, expose through new workflow |
| Survey import and geometry | Preserve |
| Geodesy / projections | Preserve |
| Uncertainty / proximity calculations | Preserve and make flagship |
| Hydraulics | Preserve and extend |
| Torque & drag | Preserve and extend |
| Buckling | Preserve |
| Casing / envelopes | Preserve |
| Geomechanics | Preserve and classify by qualification |
| MSE | Preserve |
| Offset analytics | Preserve and integrate |
| Evidence / provenance | Preserve as strategic differentiator |
| Fixed reports | Preserve and redesign presentation |
| Audit history | Preserve |
| Recovery / backups | Preserve |
| FastAPI | Preserve, modularize |
| React + TypeScript | Preserve, restructure |
| Vite | Preserve for web build |
| Streamlit | Preserve as demo/research deployment |
| CI / pytest / Hypothesis | Preserve and expand |

## 4.2 Refactor rather than delete

Refactor:

- monolithic React components;
- monolithic API router composition;
- direct UI-to-engine coupling;
- duplicated calculation paths;
- synthetic-demo-specific UI shortcuts;
- inconsistent workspace navigation;
- inconsistent validation status presentation;
- CSS accumulated from prototype phases;
- domain logic embedded in API routes;
- engineering state embedded in components.

## 4.3 Retire gradually

Retire only after replacements pass regression:

- legacy navigation;
- duplicate pages;
- obsolete feature naming;
- “M1–M17” / “17 modules” user-facing terminology;
- prototype-only visualizations superseded by the synchronized plotting / 3D system;
- deprecated endpoint aliases;
- duplicated synthetic fixture loaders.

---

# 5. Target System Context

```text
                               ┌────────────────────────────┐
                               │        GeoDrill Pro        │
                               │ v0.9 Engineering Platform  │
                               └──────────────┬─────────────┘
                                              │
                    ┌─────────────────────────┼──────────────────────────┐
                    │                         │                          │
                    ▼                         ▼                          ▼
             React Web UI               Desktop Shell             Streamlit
             Primary client             Tauri target              Demo/Research
                    │                         │                          │
                    └─────────────────────────┼──────────────────────────┘
                                              │
                                       FastAPI Gateway
                                              │
             ┌────────────────────────────────┼────────────────────────────────┐
             │                                │                                │
             ▼                                ▼                                ▼
      Domain Services                 Engineering Kernel                 Realtime
                                       / Calculation API                 Services
             │                                │                                │
             ├───────────────┐                │                 ┌───────────────┤
             ▼               ▼                ▼                 ▼               ▼
      Project Store      Evidence Store     Models          WITSML/ETP      Replay
             │               │                │                 │               │
             └───────────────┴────────────────┴─────────────────┴───────────────┘
                                              │
                 ┌────────────────────────────┼────────────────────────────┐
                 ▼                            ▼                            ▼
           Local persistence           Enterprise DB                Object store
        SQLite / DuckDB / Parquet    PostgreSQL/PostGIS/Timescale     S3 / MinIO
```

---

# 6. Architecture Principles

1. **Engineering authority lives in the engineering kernel, not the UI.**
2. **All calculations consume canonical SI inputs.**
3. **Input provenance is immutable.**
4. **A result may be calculated, withheld, invalid, stale, superseded, or unqualified.**
5. **3D renders engineering geometry; it does not become the engineering authority.**
6. **Realtime ingestion is read-only in v0.9.**
7. **Every derived channel records source channels, equation/model, version, units, and time basis.**
8. **Research models are clearly separated from qualified deterministic models.**
9. **Plan, actual, scenario, and historical data must never be visually or semantically conflated.**
10. **Every engineering workspace supports evidence, assumptions, model version, and limitations.**
11. **No silent unit conversion.**
12. **No silent coordinate reference conversion.**
13. **No silent missing-data interpolation for authoritative calculations.**
14. **No proprietary interface copying; GeoDrill must have original visual identity and UX.**

---

# 7. Recommended Monorepo Structure

```text
geodrill-pro/
│
├── apps/
│   ├── web/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── features/
│   │   │   ├── components/
│   │   │   ├── visualization/
│   │   │   ├── design-system/
│   │   │   ├── assets/
│   │   │   └── workers/
│   │   └── tests/
│   │
│   ├── desktop/
│   │   ├── src-tauri/
│   │   └── sidecar/
│   │
│   └── streamlit/
│       ├── app.py
│       └── cloud.py
│
├── services/
│   ├── api/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── dependencies/
│   │   ├── middleware/
│   │   ├── schemas/
│   │   └── errors/
│   │
│   ├── application/
│   │   ├── projects/
│   │   ├── wells/
│   │   ├── trajectories/
│   │   ├── engineering_cases/
│   │   ├── evidence/
│   │   ├── reports/
│   │   └── qualification/
│   │
│   ├── realtime/
│   │   ├── ingest/
│   │   ├── normalize/
│   │   ├── quality/
│   │   ├── derived/
│   │   ├── replay/
│   │   └── websocket/
│   │
│   ├── workers/
│   │   ├── calculations/
│   │   ├── reports/
│   │   ├── imports/
│   │   └── exports/
│   │
│   └── integrations/
│       ├── witsml/
│       ├── etp/
│       ├── las/
│       ├── csv/
│       ├── json/
│       └── osdu/
│
├── packages/
│   ├── domain/
│   │   ├── projects/
│   │   ├── wells/
│   │   ├── wellbores/
│   │   ├── trajectories/
│   │   ├── surveys/
│   │   ├── targets/
│   │   ├── casing/
│   │   ├── bha/
│   │   ├── formations/
│   │   ├── realtime/
│   │   └── evidence/
│   │
│   ├── engineering/
│   │   ├── directional/
│   │   ├── uncertainty/
│   │   ├── anticollision/
│   │   ├── geodesy/
│   │   ├── hydraulics/
│   │   ├── torque_drag/
│   │   ├── buckling/
│   │   ├── casing/
│   │   ├── bha/
│   │   ├── hole_cleaning/
│   │   ├── surge_swab/
│   │   ├── geomechanics/
│   │   ├── performance/
│   │   └── units/
│   │
│   ├── research/
│   │   ├── anomaly/
│   │   ├── clustering/
│   │   ├── dynamics/
│   │   ├── bit_condition/
│   │   └── experimental/
│   │
│   ├── contracts/
│   │   ├── api/
│   │   ├── events/
│   │   └── schemas/
│   │
│   └── streaming/
│       ├── schemas/
│       ├── wire/
│       ├── capture/
│       └── clients/
│
├── qualification/
│   ├── directional/
│   ├── anticollision/
│   ├── hydraulics/
│   ├── torque_drag/
│   ├── casing/
│   ├── geomechanics/
│   └── reference_datasets/
│
├── data/
│   ├── fixtures/
│   ├── demonstrations/
│   └── schemas/
│
├── docs/
│   ├── architecture/
│   ├── models/
│   ├── qualification/
│   ├── security/
│   ├── ui/
│   ├── branding/
│   └── evidence/
│
├── tests/
│   ├── unit/
│   ├── property/
│   ├── contract/
│   ├── integration/
│   ├── e2e/
│   ├── qualification/
│   ├── visual/
│   └── release/
│
└── tools/
```

---

# 8. Frontend Stack

## 8.1 Core

Recommended:

- React 19
- TypeScript
- Vite
- TanStack Router
- TanStack Query
- Zustand for workstation/UI state
- Zod for client-side contract validation
- React Hook Form for engineering forms
- Web Workers for expensive client-side transforms

### Why retain React

React remains appropriate because v0.9 requires:

- high-density engineering workspaces;
- synchronized tables / plots / 3D;
- docking panels;
- realtime state;
- multi-selection;
- keyboard commands;
- complex forms;
- virtualized datasets;
- modular feature ownership.

## 8.2 State categories

Do not store all state in one global store.

### Server state

Use TanStack Query for:

- projects;
- wells;
- wellbores;
- surveys;
- studies;
- calculations;
- reports;
- evidence;
- users;
- permissions.

### Workstation state

Use Zustand for:

- selected project;
- active well;
- active revision;
- selected trajectory;
- selected survey station;
- active workspace;
- panel layout;
- synchronized cursor;
- plot ranges;
- 3D camera state;
- selected 3D object;
- unit display preferences;
- theme;
- open tabs.

### Ephemeral form state

React Hook Form:

- engineering scenario editors;
- survey editors;
- target editors;
- mud program;
- BHA;
- casing strings;
- model parameters.

---

# 9. Docking / Workstation Shell

GeoDrill should behave like engineering desktop software rather than a dashboard.

Recommended application shell:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ GeoDrill Pro | Project / Well / Revision | Search | Sync | User       │
├───────────┬───────────────────────────────────────────┬────────────────┤
│ Workspace │                                           │ Property       │
│ Navigator │              Main Canvas                  │ Inspector      │
│           │                                           │                │
│ Projects  │  2D / 3D / plots / tables / workflows   │ Selection      │
│ Planning  │                                           │ Parameters     │
│ Direction │                                           │ Evidence       │
│ Survey    │                                           │ Limits         │
│ Collision │                                           │ Qualification  │
├───────────┴───────────────────────────────────────────┴────────────────┤
│ Events | warnings | validation | model | units | coordinate ref       │
└────────────────────────────────────────────────────────────────────────┘
```

Recommended docking options:

- FlexLayout
- Golden Layout

Selection should be synchronized across:

- project tree;
- tables;
- charts;
- 2D map;
- section view;
- 3D scene;
- inspector.

---

# 10. Engineering Data Grid

Required behavior:

- virtualization;
- pinned columns;
- editable cells;
- immutable input mode;
- column units;
- validation states;
- filtering;
- grouping;
- column visibility;
- copy/paste;
- CSV export;
- controlled Excel import where allowed;
- engineering precision formatting;
- row provenance;
- conditional formatting;
- keyboard navigation.

Recommended:

- AG Grid if commercial licensing is acceptable;
- otherwise TanStack Table + TanStack Virtual with custom engineering behavior.

Every numeric column should have:

```text
value
display unit
canonical SI unit
precision
nullable policy
validation status
source/provenance
```

---

# 11. Plotting Architecture

Use different engines for different workloads.

## 11.1 Engineering plots

Recommended:

- Apache ECharts for general engineering plots;
- Plotly only where specialized scientific interaction accelerates development;
- uPlot for high-frequency realtime trend panels.

## 11.2 Plot synchronization

A central `ViewportCoordinator` should synchronize:

- selected MD;
- selected TVD;
- time cursor;
- active interval;
- selected event;
- selected survey station.

Example:

```text
Select MD = 2510 m in survey table
     ↓
2D plan highlights station
     ↓
Section highlights station
     ↓
3D camera centers station
     ↓
Torque/drag plot shows depth cursor
     ↓
Hydraulics plot shows same depth cursor
```

---

# 12. 3D Subsystem

## 12.1 Technology

Primary:

- Three.js
- React Three Fiber
- Drei
- custom shaders where required

Optional large-area / geographic view:

- CesiumJS

Optional map / 2.5D:

- deck.gl
- MapLibre GL

## 12.2 Authoritative geometry flow

```text
Survey / Plan Inputs
       ↓
Engineering Directional Kernel
       ↓
Canonical trajectory stations
       ↓
Coordinate transformation
       ↓
Engineering scene model
       ↓
Three.js renderer
```

Three.js must not independently derive authoritative trajectory values.

## 12.3 Scene graph

```text
GeoDrillScene
├── SurfaceGroup
│   ├── Terrain
│   ├── Pad
│   ├── Rig
│   └── LeaseBoundary
│
├── GeologicalGroup
│   ├── FormationSurfaces
│   ├── Faults
│   ├── Targets
│   └── PressureWindows
│
├── WellsGroup
│   ├── PlannedTrajectory
│   ├── ActualTrajectory
│   ├── OffsetWells
│   ├── SurveyStations
│   ├── Casing
│   ├── HoleSections
│   └── BHA
│
├── UncertaintyGroup
│   ├── EOU
│   ├── SeparationLines
│   └── ClosestApproach
│
└── AnnotationGroup
    ├── Labels
    ├── DepthMarkers
    ├── Warnings
    └── MeasurementTools
```

## 12.4 Required 3D interactions

- orbit;
- pan;
- zoom;
- fit selected;
- fit well;
- fit target;
- select well;
- select station;
- select target;
- measure distance;
- vertical exaggeration;
- clipping plane;
- section plane;
- formation visibility;
- trajectory visibility;
- planned/actual toggle;
- uncertainty toggle;
- casing toggle;
- BHA toggle;
- label density control.

## 12.5 Coordinate handling

Every 3D scene must display:

- coordinate reference system;
- grid convergence if relevant;
- north reference;
- datum;
- elevation reference;
- local origin;
- unit system.

No geometry should render without known coordinate context unless explicitly marked local / unreferenced.

## 12.6 Performance

Use:

- instanced meshes;
- BufferGeometry;
- LOD;
- worker-based mesh generation;
- typed arrays;
- spatial indexing;
- incremental scene updates.

Avoid rebuilding the entire scene when one survey station changes.

---

# 13. UI / UX Information Architecture

## 13.1 Primary navigation

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

No “17 modules” navigation.

## 13.2 Project Hub

Panels:

- recent projects;
- fields;
- wells;
- project health;
- modified date;
- owner;
- review state;
- import;
- restore;
- create project.

## 13.3 Well Planning

Layout:

- project tree left;
- main 2D plan / section center;
- target / plan inspector right;
- well plan table bottom.

Functions:

- create target;
- define kickoff;
- create planned trajectory;
- compare scenarios;
- apply constraints;
- preview DLS;
- compare target intercept;
- save revision.

## 13.4 Directional

Functions:

- survey station table;
- planned trajectory;
- actual trajectory;
- minimum curvature;
- DLS;
- build/turn rates;
- TVD;
- North/East;
- vertical section;
- coordinate transformation;
- survey program.

## 13.5 Survey

Functions:

- survey import;
- tool metadata;
- north reference;
- corrections;
- survey quality;
- survey station validation;
- survey revision;
- error model;
- uncertainty diagnostics.

## 13.6 Anti-Collision

Panels:

- subject well;
- selected offsets;
- separation table;
- SF trend;
- closest approach;
- 3D uncertainty;
- warning list;
- exclusion rules;
- uncertainty metadata.

Output must distinguish:

- proximity calculated;
- clearance withheld;
- qualified;
- unqualified;
- incomplete evidence.

## 13.7 3D Well Model

Full-screen engineering viewport with:

- project tree;
- scene layers;
- selected-object inspector;
- coordinates;
- section clipping;
- target visibility;
- formation visibility;
- offset wells;
- uncertainty;
- casing;
- BHA;
- export screenshot;
- saved camera/bookmarks.

## 13.8 Hydraulics

Panels:

- mud properties;
- rheology;
- temperature assumptions;
- string geometry;
- annulus;
- bit/nozzles;
- pump;
- pressure profile;
- ECD;
- sensitivity;
- model limitations;
- scenario comparison.

## 13.9 Torque & Drag

Panels:

- string components;
- trajectory;
- friction factors;
- pickup/slackoff;
- rotating;
- hookload;
- torque;
- axial force;
- contact;
- buckling status;
- calibration evidence.

## 13.10 Casing

Panels:

- hole sections;
- casing strings;
- grades;
- weights;
- connections;
- loads;
- burst;
- collapse;
- tension;
- design factors;
- envelope;
- scenario comparison.

## 13.11 BHA

Panels:

- BHA component editor;
- bit;
- motor;
- RSS;
- MWD/LWD;
- stabilizers;
- drill collars;
- HWDP;
- geometry;
- tool metadata.

## 13.12 Geomechanics

Panels:

- formations;
- survey binding;
- core / LOT / FIT evidence;
- stress model;
- pore pressure;
- fracture pressure;
- wellbore stability;
- model qualification;
- limitations.

## 13.13 Realtime

Panels:

- rig connection status;
- channel browser;
- channel quality;
- depth-based view;
- time-based view;
- plan vs actual;
- events;
- derived channels;
- replay;
- latency.

## 13.14 Offsets

Functions:

- select cohort;
- harmonize;
- exclusions;
- distributions;
- duration;
- cost;
- NPT;
- performance;
- offset comparison;
- evidence.

## 13.15 Evidence

Functions:

- evidence search;
- input source files;
- hashes;
- calculations;
- model versions;
- citations;
- provenance;
- review notes.

## 13.16 Reports

- fixed evidence snapshot;
- engineering summary;
- plan summary;
- directional report;
- anti-collision report;
- hydraulics report;
- torque/drag report;
- post-well report;
- audit report.

---

# 14. GeoDrill Pro Brand System

## 14.1 Brand concept

GeoDrill branding should remain original.

Brand mark concept:

- **G** = GeoDrill;
- curved trajectory = directional well;
- target = well objective;
- layered strata = subsurface;
- rig / surface marker = drilling context.

## 14.2 Core palette

Recommended baseline:

| Token | Value | Use |
|---|---|---|
| Deep Blue | `#0B3D91` | primary brand / trust |
| Teal | `#0EA5B7` | technology / insight |
| Graphite | `#374151` | structure / text |
| Stone | `#94A3B8` | secondary surfaces |
| Orange | `#F97316` | target / focus |
| Success | `#10B981` | valid / on track |
| Warning | `#F59E0B` | caution |
| Danger | `#EF4444` | violation / critical |
| Info | `#3B82F6` | information |
| Background | `#F8FAFC` | light app background |
| Surface | `#FFFFFF` | cards/panels |
| Border | `#E2E8F0` | separators |
| Text | `#0F172A` | primary text |

## 14.3 Feature symbols

Production icon names:

```text
icon-projects
icon-well-planning
icon-directional
icon-survey
icon-anti-collision
icon-3d-well
icon-hydraulics
icon-torque-drag
icon-casing
icon-bha
icon-geomechanics
icon-realtime
icon-offsets
icon-evidence
icon-reports
icon-qualification
icon-admin
```

## 14.4 Icon rules

- 32 × 32 canonical grid;
- optimized 16 / 20 / 24 / 32 px;
- SVG preferred;
- monochrome version available;
- colored version reserved for workspace identification;
- use `currentColor` for navigation icons where possible;
- avoid gradients for tiny toolbar icons;
- do not use vendor logos;
- do not visually copy COMPASS, DrillPlan, or other proprietary icon sets.

---

# 15. Design System

## 15.1 Typography

Recommended:

- Inter or Plus Jakarta Sans

Scale:

```text
Display      32–40 px
H1           28–32 px
H2           22–24 px
H3           16–18 px
Body         14 px
Small        12–13 px
Caption      11–12 px
Numeric KPI  20–28 px tabular
```

Engineering numerical values should use tabular numerals.

## 15.2 Density

GeoDrill must support:

- Comfortable density;
- Compact engineering density.

Tables default to compact mode for professional use.

## 15.3 Status semantics

```text
Valid / On Track          Green
Information               Blue
Warning / Approaching     Amber
Violation / Critical      Red
Not analysed              Gray
Withheld                  Graphite / striped
Stale                     Purple or neutral warning
Research                  Teal outline
Unqualified               Amber outline
```

Never rely only on color. Add:

- icon;
- label;
- tooltip;
- reason.

---

# 16. Backend Architecture

## 16.1 FastAPI remains the primary API boundary

Refactor `services/api/main.py` into routers.

Example:

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

Routes should orchestrate application services. They should not contain engineering equations.

## 16.2 Domain / application separation

```text
HTTP Router
    ↓
Application Service
    ↓
Domain Model
    ↓
Engineering Kernel / Repository / Event
```

Example:

```text
POST /projects/{id}/hydraulics/cases
        ↓
CreateHydraulicsCase
        ↓
validate domain context
        ↓
HydraulicsKernel.calculate()
        ↓
save inputs/result/provenance
        ↓
emit CalculationCompleted
```

---

# 17. Engineering Kernel Architecture

## 17.1 Model classes

Every engineering model must belong to one class:

### A. Deterministic / Verified

Examples:

- minimum curvature;
- coordinate transformation;
- deterministic pressure balance;
- selected hydraulics;
- documented casing equations.

### B. Deterministic / Research

Implemented but not independently qualified.

### C. Statistical / ML

Examples:

- anomaly detection;
- clustering;
- offset empirical distributions.

### D. Operational decision support

Combines calculations and rules, but must not imply automatic authority.

## 17.2 Calculation envelope

Every engineering model result should use a common envelope:

```json
{
  "calculation_id": "...",
  "model": "hydraulics.hb_annular_pressure_loss",
  "model_version": "0.9.0",
  "qualification": "research",
  "status": "calculated",
  "inputs_hash": "...",
  "geometry_revision_id": "...",
  "result": {},
  "assumptions": [],
  "warnings": [],
  "limitations": [],
  "evidence_ids": [],
  "created_at": "...",
  "software_revision": "..."
}
```

Status values:

```text
calculated
withheld
invalid
failed
stale
superseded
not_applicable
```

## 17.3 Units

Architecture:

```text
External units
     ↓
Import/API boundary
     ↓
Explicit conversion
     ↓
Canonical SI
     ↓
Engineering core
     ↓
Canonical SI result
     ↓
Presentation unit conversion
```

Do not pass UI display units into kernel equations.

---

# 18. Data Model

## 18.1 Core hierarchy

```text
Organization
└── Project
    ├── Field
    ├── CoordinateReference
    ├── Evidence
    └── Well
        └── Wellbore
            ├── TrajectoryRevision
            ├── SurveyRevision
            ├── Targets
            ├── FormationModel
            ├── HoleSections
            ├── CasingProgramme
            ├── BHAProgramme
            ├── MudProgramme
            ├── EngineeringCases
            └── RealtimeRuns
```

## 18.2 Major entities

### Project

```text
id
name
description
owner
organization_id
datum
default_crs
default_unit_profile
created_at
updated_at
status
```

### Well

```text
id
project_id
name
uwi
surface_location
rkb_elevation
spud_date
status
```

### Wellbore

```text
id
well_id
name
sidetrack_parent
wellbore_type
planned_td
status
```

### TrajectoryRevision

```text
id
wellbore_id
revision
type: planned | actual | scenario
survey_revision_id
coordinate_reference_id
status
created_by
approved_by
created_at
```

### SurveyStation

```text
md_m
inc_rad
azi_rad
tvd_m
north_m
east_m
dls_rad_m
tool_code
quality
source_row
```

### Target

```text
id
wellbore_id
name
geometry_type
center_xyz
radius / box
orientation
tolerance
formation_id
```

### Formation

```text
id
name
top_surface
base_surface
uncertainty
source_evidence
```

### CasingString

```text
name
top_md
shoe_md
od
id
weight
grade
connection
design_factors
```

### BHA

```text
id
name
components[]
bit
motor/rss
mwd
lwd
stabilizers
total_length
```

### EngineeringCase

```text
id
wellbore_id
case_type
geometry_revision
input_document
input_hash
result_document
model
model_version
qualification
status
```

---

# 19. Persistence Architecture

## 19.1 Local mode

Keep:

- SQLite
- DuckDB
- Parquet
- raw object files

Recommended responsibilities:

```text
SQLite   → transactions / metadata / project state
Parquet  → tabular datasets / timeseries snapshots
DuckDB   → local analytical queries
Raw      → immutable source bytes
```

## 19.2 Enterprise mode

Recommended:

- PostgreSQL
- PostGIS
- TimescaleDB extension where suitable
- S3 / MinIO
- Redis optional
- NATS JetStream optional for event / streaming backbone

```text
PostgreSQL → project and engineering metadata
PostGIS    → spatial geometry
Timescale  → realtime / dense time-series
S3/MinIO   → immutable source files, reports, exports
Redis      → cache, sessions, short-lived coordination
NATS       → realtime events / durable internal streams
```

## 19.3 Repository interfaces

Application services should depend on interfaces:

```python
class ProjectRepository: ...
class WellRepository: ...
class SurveyRepository: ...
class CalculationRepository: ...
class EvidenceRepository: ...
class RealtimeRepository: ...
```

Local and enterprise backends implement the same contracts.

---

# 20. Realtime Architecture

## 20.1 v0.9 scope

Realtime must be **read-only**.

```text
Rig / EDR
    ↓
WITSML / ETP
    ↓
Connector
    ↓
Raw capture
    ↓
Normalization
    ↓
Quality
    ↓
Canonical channels
    ↓
Derived channels
    ↓
Timeseries store
    ↓
WebSocket
    ↓
Realtime workspace
```

## 20.2 Connector responsibilities

- authentication;
- subscription;
- reconnect;
- heartbeat;
- duplicate detection;
- vendor mapping;
- schema version;
- source timestamps;
- arrival timestamps;
- sequence IDs;
- raw payload preservation.

## 20.3 Canonical channel model

```json
{
  "channel_id": "spp",
  "source_name": "Standpipe Pressure",
  "source_unit": "psi",
  "canonical_unit": "Pa",
  "value_si": 21900000,
  "source_time": "...",
  "arrival_time": "...",
  "quality": "valid",
  "source": "WITSML",
  "wellbore_id": "...",
  "run_id": "..."
}
```

## 20.4 Quality states

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

## 20.5 Derived channels

Example MSE:

```text
WOB + Torque + RPM + ROP + Bit Diameter
             ↓
          MSE engine
             ↓
MSE value + status + reason + source references
```

Derived data must never overwrite raw channels.

---

# 21. Replay / Simulation

Replay service must support:

- source-time replay;
- arrival-time replay;
- seek;
- pause;
- speed;
- gap preservation;
- deterministic test playback;
- fixture playback;
- historical rig replay.

The replay engine should use the same canonical event path as live ingestion where possible.

---

# 22. Events and Messaging

Recommended internal event types:

```text
ProjectCreated
WellCreated
WellboreCreated
SurveyImported
SurveyRevisionAccepted
TrajectoryCalculated
GeometryRevisionCreated
TargetUpdated
CalculationRequested
CalculationCompleted
CalculationWithheld
CalculationFailed
EvidenceAttached
ReportGenerated
RealtimeChannelReceived
RealtimeQualityChanged
EngineeringResultStale
ApprovalRequested
ApprovalCompleted
```

Every event should include:

```text
event_id
event_type
project_id
entity_id
actor
timestamp
software_revision
payload
correlation_id
```

---

# 23. Calculation Staleness / Dependency Graph

This should become a flagship v0.9 capability.

Example:

```text
Trajectory Revision Changed
        │
        ├── Anti-Collision      → STALE
        ├── Torque & Drag       → STALE
        ├── Hydraulics          → STALE if geometry-dependent
        ├── Casing Loads        → STALE
        ├── Geomechanics        → STALE if survey-bound
        └── Reports             → STALE
```

Implement a dependency graph.

A calculation must reference:

- geometry revision;
- survey revision;
- formation revision;
- mud program revision;
- BHA revision;
- casing revision;
- model version.

No stale result should appear current without a visible warning.

---

# 24. API Design

Base:

```text
/api/v1
```

Examples:

```text
GET    /projects
POST   /projects
GET    /projects/{project_id}

GET    /projects/{project_id}/wells
POST   /projects/{project_id}/wells

GET    /wellbores/{wellbore_id}/trajectories
POST   /wellbores/{wellbore_id}/trajectories

POST   /wellbores/{wellbore_id}/surveys/import
POST   /wellbores/{wellbore_id}/directional/calculate
POST   /wellbores/{wellbore_id}/anticollision/calculate

POST   /wellbores/{wellbore_id}/hydraulics/cases
POST   /wellbores/{wellbore_id}/torque-drag/cases
POST   /wellbores/{wellbore_id}/casing/cases
POST   /wellbores/{wellbore_id}/geomechanics/cases

GET    /projects/{project_id}/evidence
GET    /projects/{project_id}/reports

GET    /realtime/runs
GET    /realtime/runs/{id}/channels
WS     /realtime/runs/{id}/stream
```

---

# 25. Authentication and Authorization

## 25.1 Local mode

- local identity;
- optional OS user binding;
- encrypted signing key;
- project roles.

## 25.2 Enterprise mode

Preferred:

- OIDC;
- OAuth 2.1;
- Microsoft Entra ID / Keycloak / Auth0 depending deployment;
- MFA delegated to identity provider.

## 25.3 RBAC

Roles:

```text
Viewer
Engineer
Author
Reviewer
Approver
Project Admin
Organization Admin
```

Permission examples:

```text
project.read
project.write
survey.import
survey.accept
calculation.execute
calculation.review
programme.modify
report.generate
report.approve
evidence.attach
admin.users
admin.security
```

Four-eyes rule:

- author cannot approve their own controlled revision where configured.

---

# 26. Security Architecture

Required:

- TLS in server deployments;
- encrypted secrets;
- signed releases;
- dependency scanning;
- SBOM;
- SAST;
- file import sandboxing;
- ZIP/archive traversal protection;
- strict XML parsing;
- rate limiting;
- audit logging;
- backup encryption;
- restore verification;
- least privilege;
- CSP;
- secure headers;
- upload size limits;
- content-type validation.

Never:

- commit certificates;
- commit private signing keys;
- embed production secrets in desktop bundle;
- execute imported project content.

---

# 27. Desktop Strategy

## 27.1 v0.9 target

Tauri 2 is recommended as the future desktop shell.

```text
Tauri
├── React frontend
├── local FastAPI sidecar
├── local engineering kernels
├── local storage
└── updater / signing
```

## 27.2 Migration

Do not block v0.9 development on Tauri.

Stages:

1. retain existing launcher;
2. build new React workstation;
3. stabilize API contracts;
4. introduce Tauri;
5. run FastAPI as managed sidecar;
6. add signed updater;
7. retire legacy desktop launch path only after release acceptance.

---

# 28. Streamlit Strategy

Streamlit remains useful for:

- public research demonstration;
- simplified cloud preview;
- stakeholder review;
- non-sensitive synthetic workflows.

It should not be the primary v0.9 workstation.

---

# 29. Reports and Evidence

Every report should include:

- project;
- well;
- wellbore;
- revision;
- model;
- model version;
- input hashes;
- source evidence;
- coordinate reference;
- units;
- assumptions;
- warnings;
- limitations;
- qualification state;
- generated timestamp;
- software revision.

Report types:

```text
Well Plan Summary
Directional Survey Report
Anti-Collision Report
Hydraulics Report
Torque & Drag Report
Casing Design Report
Geomechanics Report
Realtime Operations Summary
Post-Well Review
Offset Benchmark Report
Evidence Package
Audit Package
```

---

# 30. Qualification Strategy

## 30.1 Four levels

```text
IMPLEMENTED
    ↓
VERIFIED
    ↓
BENCHMARKED
    ↓
INDEPENDENTLY QUALIFIED
```

Do not collapse these into one “complete” state.

## 30.2 Engineering model status

```text
Research
Internal Verification
Published Benchmark
Independent Review
Qualified for declared envelope
```

## 30.3 Test hierarchy

### Unit

- equation-level;
- deterministic edge cases.

### Property

Hypothesis tests:

- invariants;
- monotonicity;
- round trips;
- conservation.

### Contract

- API schema;
- import/export;
- backwards compatibility.

### Integration

- persisted project;
- input → calculation → report;
- save / reopen.

### End-to-end

- browser workflow;
- desktop workflow.

### Qualification

- published datasets;
- known benchmarks;
- cross-software comparison where permitted;
- independent engineering review.

### Release

- clean-machine install;
- run;
- import;
- calculate;
- backup;
- restore;
- uninstall;
- hash verify;
- signature verify.

---

# 31. 3D Validation

3D testing must include:

- trajectory coordinates match kernel outputs;
- unit scaling;
- vertical exaggeration does not alter engineering values;
- picking returns correct entity IDs;
- selected MD matches survey station;
- formation surface coordinates use correct CRS;
- uncertainty ellipsoid axes match covariance decomposition;
- closest-approach geometry matches engineering result.

Visual regression alone is insufficient.

---

# 32. UI Testing

Recommended:

- Vitest
- React Testing Library
- Playwright
- screenshot / visual regression
- accessibility checks
- keyboard-navigation tests

Critical flows:

```text
Create project
Create well
Import survey
Accept survey
Create trajectory
Open 3D
Run anti-collision
Run hydraulics
Save study
Reopen
Generate report
Backup
Restore
```

---

# 33. Observability

## 33.1 Local

- rotating structured logs;
- API request IDs;
- calculation IDs;
- audit chain;
- diagnostics export.

## 33.2 Enterprise

- OpenTelemetry;
- Prometheus;
- Grafana;
- centralized logs;
- trace IDs.

Metrics:

```text
API latency
calculation latency
WITSML latency
ETP reconnects
dropped messages
quarantined records
worker failures
DB latency
3D render FPS
frontend errors
report generation duration
```

---

# 34. Error Handling

Error responses should use stable codes:

```json
{
  "error": {
    "code": "SURVEY_UNKNOWN_NORTH_REFERENCE",
    "message": "North reference is required before trajectory calculation.",
    "details": {},
    "correlation_id": "..."
  }
}
```

No raw stack traces in UI.

Engineering errors must distinguish:

- invalid input;
- unsupported envelope;
- insufficient evidence;
- numerical failure;
- system failure.

---

# 35. Import / Export

Supported targets:

## v0.9

- CSV
- JSON
- LAS
- GeoDrill project archive
- report JSON / PDF
- trajectory exports

## Later / integration

- WITSML
- ETP
- OSDU-compatible mappings
- vendor-specific interchange
- GIS formats as required

Every import records:

- raw bytes hash;
- filename;
- source;
- importer version;
- mapping;
- units;
- accepted/rejected rows;
- warnings.

---

# 36. Performance Targets

Suggested engineering targets:

| Operation | Target |
|---|---:|
| Application interactive after launch | < 3 s local warm |
| Project open | < 2 s normal project |
| Survey table 100k rows | virtualized |
| 3D scene 100 wells | interactive |
| 3D picking | < 100 ms |
| Simple deterministic calculation | < 250 ms |
| complex scenario calculation | async job if > 1 s |
| realtime plot latency | < 1 s UI target |
| UI interaction | < 100 ms perceived |

Performance targets are engineering goals, not safety guarantees.

---

# 37. Worker Architecture

Synchronous:

- minimum curvature;
- small anti-collision;
- simple pressure balance.

Async:

- large offset cohorts;
- report bundles;
- large imports;
- complex 3D mesh preprocessing;
- Monte Carlo / uncertainty;
- batch scenario grids.

Local mode may initially use:

- process pool;
- background task queue.

Enterprise mode may use:

- Redis + worker;
- NATS;
- Temporal for durable workflows if needed.

Avoid adopting enterprise orchestration until real workflow requirements justify it.

---

# 38. Original GeoDrill User Experience

GeoDrill can learn from professional drilling software patterns:

- project trees;
- dense engineering grids;
- dockable panels;
- linked plots;
- 3D well views;
- engineering inspectors;
- revision workflows.

But do not copy:

- proprietary logos;
- screenshots;
- icons;
- exact layout;
- color system;
- trade dress;
- proprietary terminology where avoidable.

GeoDrill should have a distinct design language.

---

# 39. Feature Flags

Use feature flags for incomplete capabilities.

Example:

```text
realtime_witsml
etp_streaming
enterprise_auth
advanced_3d
uncertainty_3d
research_anomaly
research_dynamics
tauri_shell
```

Feature flags do not substitute for authorization.

---

# 40. Versioning

Version separately:

```text
Application Version
API Version
Model Version
Import Schema Version
Project Archive Version
Report Schema Version
Realtime Schema Version
```

A software update must not silently change prior saved calculation results.

---

# 41. Backward Compatibility

When old project data is opened:

```text
archive_version
     ↓
migration planner
     ↓
preflight
     ↓
atomic migration
     ↓
verification
     ↓
open project
```

Preserve:

- original archive;
- original hashes;
- migration log;
- rollback option.

---

# 42. v0.9 Implementation Roadmap

## Phase 0 — Baseline Freeze

Goal:

Preserve v0.8 research baseline.

Actions:

- tag current baseline;
- record release hashes;
- preserve tests;
- freeze existing model behavior;
- create `v0.9-workstation` branch;
- document known limitations.

Acceptance:

- current regression passes;
- current release can still be built;
- backup/restore verified.

---

## Phase 1 — Architecture Refactor

Build:

- domain package;
- application services;
- modular API routers;
- common calculation envelope;
- calculation dependency graph;
- standardized errors.

Acceptance:

- existing engineering tests unchanged or intentionally migrated;
- no regression in current calculations;
- `main.py` reduced to composition/bootstrap responsibilities.

---

## Phase 2 — Design System & App Shell

Build:

- GeoDrill logo integration;
- feature SVG icon package;
- design tokens;
- sidebar;
- top bar;
- project/well context;
- command palette;
- docking framework;
- light/dark themes.

Acceptance:

- no user-facing “17 modules” terminology;
- responsive workstation shell;
- keyboard navigation;
- persistent panel layout.

---

## Phase 3 — Project / Well Domain

Build:

- Project;
- Field;
- Well;
- Wellbore;
- Revision;
- target hierarchy;
- project tree.

Acceptance:

- user can create/open/edit a project and well;
- existing data migrates;
- project tree drives workspace context.

---

## Phase 4 — Directional Flagship Workflow

Build:

- well plan editor;
- survey grid;
- trajectory;
- planned vs actual;
- DLS;
- targets;
- coordinate reference;
- uncertainty;
- anti-collision;
- synchronized plots.

Acceptance:

- end-to-end plan → survey → uncertainty → collision workflow;
- all calculations source-backed;
- staleness behavior works.

---

## Phase 5 — 3D Engineering Workspace

Build:

- R3F/Three scene;
- planned well;
- actual well;
- offsets;
- targets;
- formations;
- casing;
- BHA;
- uncertainty;
- collision visualization;
- inspector.

Acceptance:

- 3D coordinates match kernel;
- table/plot/3D selection synchronized;
- scene remains interactive under representative load.

---

## Phase 6 — Engineering Workspaces

Integrate:

- hydraulics;
- torque & drag;
- buckling;
- casing;
- BHA;
- geomechanics;
- drilling performance.

Acceptance:

- common engineering case behavior;
- common assumptions/limitations panel;
- source revision binding;
- scenario compare;
- report generation.

---

## Phase 7 — Realtime Foundation

Build:

- canonical channel model;
- raw capture;
- replay;
- quality;
- WebSocket;
- read-only WITSML adapter;
- read-only ETP adapter.

Acceptance:

- live and replay use compatible internal event flow;
- reconnect tested;
- deduplication tested;
- source vs arrival time preserved;
- no write routes.

---

## Phase 8 — Desktop

Build:

- Tauri shell;
- managed FastAPI sidecar;
- local data dir;
- IPC/health;
- signing;
- updater;
- rollback.

Acceptance:

- clean install;
- launch;
- calculate;
- close;
- backup;
- restore;
- update;
- rollback;
- uninstall;
- user data retained.

---

## Phase 9 — Enterprise

Build:

- PostgreSQL;
- PostGIS;
- Timescale;
- object store;
- OIDC;
- RBAC;
- multi-user;
- audit;
- centralized monitoring.

Acceptance:

- tenant/project isolation;
- role testing;
- restore testing;
- external security review plan.

---

## Phase 10 — Qualification

Build evidence package:

- published benchmarks;
- real authorized datasets;
- model residuals;
- holdout tests;
- independent reviews;
- field acceptance.

Acceptance must be model-specific.

---

# 43. Definition of Done for v0.9

GeoDrill Pro v0.9 should not be called complete solely because the UI exists.

Minimum definition:

### Product

- domain-based navigation;
- no “17 modules” framing;
- coherent project → well → workflow hierarchy.

### UI

- GeoDrill brand;
- feature icons;
- dockable workstation;
- light/dark themes;
- synchronized tables / plots / 3D.

### Directional

- well planning;
- surveys;
- uncertainty;
- anti-collision;
- 3D.

### Engineering

- core drilling engineering workspaces connected.

### Data

- migration;
- revision model;
- provenance;
- dependency/staleness.

### Realtime

- at least replay + canonical realtime model;
- read-only live adapter where feasible.

### Desktop

- reliable local workstation distribution.

### Quality

- numerical regression;
- API contract tests;
- UI E2E;
- release tests;
- security controls.

---

# 44. Build vs Buy Matrix

| Capability | Recommendation |
|---|---|
| React | Keep/build |
| UI primitives | Radix / shadcn-style primitives or custom |
| Data grid | AG Grid or TanStack-based |
| Docking | FlexLayout / Golden Layout |
| Charts | ECharts + uPlot |
| 3D | Three.js / React Three Fiber |
| Global geospatial | Cesium optional |
| 2D mapping | MapLibre / deck.gl optional |
| API | FastAPI |
| Validation | Pydantic |
| Local DB | SQLite |
| Analytics | DuckDB / Parquet |
| Enterprise DB | PostgreSQL |
| Spatial DB | PostGIS |
| Time series | TimescaleDB |
| Object store | S3 / MinIO |
| Event bus | NATS optional |
| Cache | Redis optional |
| Desktop | Tauri 2 |
| Auth | external OIDC provider |
| Observability | OpenTelemetry |
| CI | GitHub Actions |
| Python testing | pytest + Hypothesis |
| Browser testing | Playwright |
| Frontend unit | Vitest |

---

# 45. Major Risks

## Scope creep

Mitigation:

- directional + 3D as flagship;
- engineering features grouped by priority;
- research features behind classification.

## Validation debt

Mitigation:

- model qualification state;
- source references;
- benchmark registry;
- independent review.

## Unit errors

Mitigation:

- SI kernel;
- boundary conversion;
- unit metadata;
- unit tests.

## Coordinate errors

Mitigation:

- explicit CRS;
- explicit north reference;
- coordinate diagnostics;
- geodesy regression.

## Realtime reliability

Mitigation:

- raw capture;
- dedupe;
- reconnect;
- arrival time;
- source time;
- replay.

## 3D performance

Mitigation:

- LOD;
- instancing;
- workers;
- typed geometry;
- scene partitioning.

## IP / trade dress

Mitigation:

- original branding;
- original icons;
- original design tokens;
- feature parity without visual copying.

## Engineering liability

Mitigation:

- applicability limits;
- withheld results;
- qualification status;
- no operational authority by default.

---

# 46. Recommended v0.9 Product Statement

> **GeoDrill Pro v0.9 is a drilling engineering workstation that integrates well planning, directional engineering, survey management, anti-collision, 3D well visualization, drilling engineering calculations, realtime monitoring, offset analytics, and evidence-driven reporting in one traceable environment.**

---

# 47. Recommended v0.9 Navigation Statement

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

# 48. Final Architecture Decision

The v0.9 programme should follow this principle:

```text
CURRENT GEODRILL
       │
       ├── preserve validated engineering
       ├── preserve evidence / provenance
       ├── preserve testing
       │
       ▼
ARCHITECTURE REFACTOR
       │
       ├── domain model
       ├── modular API
       ├── shared contracts
       ├── dependency graph
       │
       ▼
WORKSTATION UI
       │
       ├── GeoDrill branding
       ├── feature icons
       ├── docking
       ├── engineering grid
       ├── synchronized plots
       │
       ▼
3D ENGINE
       │
       ├── planned
       ├── actual
       ├── offsets
       ├── formations
       ├── targets
       ├── uncertainty
       │
       ▼
REALTIME
       │
       ├── WITSML
       ├── ETP
       ├── replay
       ├── quality
       │
       ▼
ENTERPRISE + QUALIFICATION
```

GeoDrill Pro v0.9 is therefore an **upgrade of the current platform**, not a replacement.

The engineering kernel remains the computational authority. The workstation becomes the professional interaction layer. The 3D engine becomes the spatial visualization layer. The realtime system becomes the operational data layer. The evidence and qualification system becomes the trust layer.

That combination is the target architecture for the next major GeoDrill Pro release.

---

# Appendix A — Suggested Frontend Package Boundaries

```text
features/
├── projects/
├── wells/
├── planning/
├── directional/
├── survey/
├── anticollision/
├── three-d/
├── hydraulics/
├── torque-drag/
├── casing/
├── bha/
├── geomechanics/
├── realtime/
├── offsets/
├── evidence/
├── reports/
├── qualification/
└── admin/
```

Each feature:

```text
feature/
├── api/
├── components/
├── hooks/
├── pages/
├── state/
├── types/
├── validation/
└── tests/
```

---

# Appendix B — Suggested Design Token Structure

```ts
export const tokens = {
  color: {
    brand: {
      deepBlue: "#0B3D91",
      teal: "#0EA5B7",
      orange: "#F97316",
    },
    semantic: {
      success: "#10B981",
      warning: "#F59E0B",
      danger: "#EF4444",
      info: "#3B82F6",
    },
    neutral: {
      background: "#F8FAFC",
      surface: "#FFFFFF",
      border: "#E2E8F0",
      text: "#0F172A",
      textSecondary: "#475569",
      muted: "#94A3B8",
    }
  },
  spacing: {
    1: 4,
    2: 8,
    3: 12,
    4: 16,
    6: 24,
    8: 32,
    12: 48
  },
  radius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16
  }
};
```

---

# Appendix C — Feature Icon Asset Structure

```text
apps/web/src/assets/icons/
├── brand/
│   ├── geodrill-mark.svg
│   ├── geodrill-horizontal.svg
│   ├── geodrill-stacked.svg
│   └── geodrill-app-icon.svg
│
└── features/
    ├── projects.svg
    ├── well-planning.svg
    ├── directional.svg
    ├── survey.svg
    ├── anti-collision.svg
    ├── well-3d.svg
    ├── hydraulics.svg
    ├── torque-drag.svg
    ├── casing.svg
    ├── bha.svg
    ├── geomechanics.svg
    ├── realtime.svg
    ├── offsets.svg
    ├── evidence.svg
    ├── reports.svg
    ├── qualification.svg
    └── admin.svg
```

---

# Appendix D — Engineering Workspace Header Standard

Every engineering workspace should display:

```text
Project      North Ridge
Well         Well A
Wellbore     Main Bore
Revision     Plan R03
Geometry     GR-27
Model        Torque & Drag 0.9.0
Status       Research / Verified
Units        Metric
CRS          WGS84 / UTM Zone XX
Last run     YYYY-MM-DD HH:MM
```

---

# Appendix E — Standard Assumptions / Limits Panel

```text
MODEL SCOPE
  Steady state
  Single phase
  Current geometry revision

INPUT EVIDENCE
  Survey: accepted
  Mud: supplied
  String: supplied

LIMITATIONS
  No multiphase
  No thermal coupling
  No equipment authority

QUALIFICATION
  Internal verification
  Independent qualification pending
```

---

# Appendix F — Decision Support Rule

The UI must never turn a research model into a command.

Preferred wording:

```text
Potential concern detected
Review hydraulics and hole-cleaning assumptions.
```

Avoid:

```text
Increase flow rate to 850 gpm now.
```

unless future operational authority, qualified control logic, and organizational approval explicitly support that capability.

---

# Appendix G — Recommended Release Labels

```text
v0.9.0-alpha    workstation shell
v0.9.0-beta.1   directional + 3D
v0.9.0-beta.2   engineering workspaces
v0.9.0-rc.1     release candidate
v0.9.0          research / engineering workstation release
```

Model qualification status remains separate from application semantic version.

---

# Appendix H — Architectural Success Criteria

GeoDrill Pro v0.9 succeeds when:

1. the user thinks in wells and workflows, not modules;
2. one selected object remains synchronized across table, plot, 2D, and 3D;
3. every result is traceable to model version and input revision;
4. stale calculations cannot masquerade as current;
5. the UI clearly distinguishes planned, actual, historical, research, and qualified information;
6. the 3D view is engineering-consistent, not decorative;
7. realtime data is source-traceable and quality-aware;
8. local, desktop, and cloud deployments share the same domain contracts;
9. the existing verified engineering logic survives the v0.9 transition;
10. GeoDrill has its own recognizable brand, symbol system, and professional drilling-workstation identity.
