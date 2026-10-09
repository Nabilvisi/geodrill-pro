# Phase 5 engineering scene — verified selection foundation, remaining integration open

Separate branch `v09-engineering-scene`, based on b53757b. The original alpha.2 candidate, PR #4 and its Windows artifacts are preserved. This development source is not published. The full supplied architecture remains the target.

## Current evidence

- Real lazy Three.js/R3F/Drei WebGL view of persisted kernel geometry.
- Canonical N/E/positive-down coordinates map to renderer East/up/south axes with origin rebasing before Float32 conversion.
- Twenty-three numerical/identity checks, TypeScript, production build and 697 Python regression tests pass on the changed scene source.
- Saved synthetic geometry renders; table MD selection and unit/exaggeration invariance pass in the browser.
- Actual canvas clicks now select saved MD in both the standalone workstation and the real Streamlit component iframe. Client coordinates are normalized against the canvas CSS rectangle; point identity is selected by distance to the ray, then camera distance.
- Primary-source table, plan and 3D selection synchronize in both directions. SVG plan points support mouse, Enter and Space selection.
- Feet and vertical exaggeration x2 retain the saved metre coordinates; canonical distance between the fixture's MD 500 and 1000 is 500.000 m.
- 100k samples are covered by a data-processing check, not a representative WebGL interactivity benchmark.

## Complete phase-5 acceptance matrix

| Requirement | Status |
|---|---|
| Saved-kernel coordinate authority, units and origin | Implemented foundation; numerical checks pass |
| React Three Fiber/Three/Drei renderer | Local production build and actual synthetic rendering pass |
| Orbit, pan, zoom and fit well/selected | Implemented; broad browser interaction acceptance remains open |
| Selected station and entity picking | Primary saved-source station raycasting verified in standalone and Streamlit; other entity classes open |
| Table/plot/3D synchronization | Primary-source selection verified in both directions, including keyboard plan selection; cohort/entity scope open |
| Planned/actual/scenario/offset saved cohorts | Open |
| Targets, target picking and fit target | Open; require explicit reference context |
| Formation surfaces/faults/pressure windows | Flat interpreted top patches only; surveyed/reference-bound surfaces open |
| Casing/hole sections/BHA geometry and selection | Casing centre lines only; physical mesh, hole/BHA integration open |
| Uncertainty/covariance ellipsoid axes | Open; no generic ellipsoid substitute |
| Closest approach and separation lines | Open; must consume exact saved engineering result |
| Canonical distance measurement | Numerical and actual browser acceptance pass on the saved synthetic fixture |
| Vertical exaggeration | Display-only; numerical and visible value invariance pass |
| Clipping and section planes | Open |
| All visibility toggles and label-density controls | Partial; full controls open |
| CRS, datum, north, elevation, origin, units and convergence disclosure | Implemented foundation; no inferred CRS conversion |
| Incremental buffers/instancing/LOD/worker/spatial index | BufferGeometry foundation; representative update/load acceptance open |
| Representative 100-well interactive load and picking latency | Open; no performance guarantee |
| WebGL failure/context-loss recovery and accessibility | Error disclosure/table foundation; full recovery/keyboard acceptance open |
| Streamlit, desktop package, full regression and release acceptance | 697 source regressions, integrity guard and actual local Streamlit WebGL/picking pass; Windows/remote scene acceptance open |

## Limits and continuation

Scene geometry never independently derives a trajectory. Formation patches are illustrative interpreted planes, not regional surveyed surfaces; casing centre lines do not model actual diameters. Unknown/mismatched context, non-finite geometry and inconsistent saved reference coordinates withhold rendering.

The current renderer chunk is 947.50 kB / 255.93 kB gzip and loads only for the 3D view. Vite's size warning and the upstream THREE.Clock deprecation remain recorded concerns. Work resumed on 9 October after allowance recovered. [Actual selection proof](evidence/v09-scene-raycast.jpg) and [machine-readable evidence](evidence/v09-scene-foundation.json) record the bounded acceptance. All remaining matrix rows retain their full architectural criteria.

The original alpha.2 candidate stays clean at b53757b in `geodrill-pro`; PR #4 is open. Public Streamlit was awakened and visibly confirmed as alpha.1 on 9 October. The scene source is not published. A separate application currently owns port 8765; isolated acceptance uses 8877 and 8888 and must not stop the unrelated service.

Equipment control is false; equipment authority is none; no automated drilling clearance or independent field qualification is provided.
