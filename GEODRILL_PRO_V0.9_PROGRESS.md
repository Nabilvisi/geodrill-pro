# GeoDrill Pro v0.9 — Implementation Progress

## Session Metadata

- Date: 9 October 2026 (Asia/Jakarta)
- Session: resumed critical phase-5 picking and distribution verification
- Repository: geodrill-pro-scene, separate worktree within Project Drill
- Branch: v09-engineering-scene
- HEAD commit: b53757b1e5d69718db712a43eacfa2363919c414 at this checkpoint; source changes are uncommitted
- Working tree: scene source, generated Streamlit bundle, CI checks and evidence documents
- Five Hour Limit Remaining: 72% at the latest live check; historical 7%/9% stop no longer applies
- Reason session stopped: not stopped; work is active. The next critical task is desktop runtime acceptance without disturbing another application on port 8765.

## Current Objective

Continue the supplied architecture in coherent verified increments. Finish the saved-coordinate scene selection and distribution checks, then saved role/offset integration. Preserve the original b53757b alpha.2 PR #4 candidate and its exact Windows artifacts. The human PR #2/alpha.1 approval has already been fulfilled; PR #4 remains unmerged.

## Architecture Phase

Phase 5 in progress. The coordinate/rendering foundation is implemented locally; the complete scene graph, cohort integration, interactions and acceptance gates remain open. No full-phase or release completion claim.

## Completed This Session

- Re-ran the numerical baseline, repaired canvas-relative pointer coordinates and nearest-ray vertex identity.
- Added real plot-point mouse and keyboard selection, connected to the shared measured-depth state.
- Verified actual WebGL clicks change MD in both the standalone workstation and the real Streamlit iframe.
- Verified 3D selection appears in the directional table/plot and keyboard plot selection returns to 3D.
- Verified foot display and vertical exaggeration x2 retain exact saved metre coordinates; canonical straight-line distance remains 500.000 m.
- Passed 23 scene checks, TypeScript, production build and 697 Python regression tests on the changed scene source.
- Rebuilt and verified the complete Streamlit component, including its lazy renderer chunk.
- Added scene/type checks to Windows/Linux CI and the release workflow; both YAML files parse.
- Rechecked GitHub: PR #2 merged, research-6 public, PR #4 open. Woke the hosted app and observed public alpha.1.
- Found a live unrelated application on port 8765; isolated verification uses 8877 and Streamlit 8888.

## Files Added

| File | Purpose |
|---|---|
| apps/desktop/src/sceneModel.ts | Canonical display transforms, frame validation, station identity and pointer/raycast helpers |
| apps/desktop/src/EngineeringSceneCanvas.tsx | Lazy saved-coordinate R3F view with bounds-aware raycast selection |
| tools/test_scene.mjs | 23 numerical/identity checks including real Three.js raycasting |
| docs/V09-ENGINEERING-SCENE.md | Complete phase-5 acceptance matrix |
| docs/evidence/v09-scene-foundation.json | Current evidence and explicitly open gates |
| docs/evidence/v09-scene-raycast.jpg | Actual standalone WebGL selection and canonical-distance proof |
| docs/evidence/v09-alpha2-handoff-from-b537.md | Preserved original candidate handoff |
| apps/streamlit/component/assets/EngineeringSceneCanvas-Ddna_1zE.js | Verified lazy renderer asset |
| apps/streamlit/component/assets/index-B5QbBp30.js | Verified current workstation asset |

## Files Modified

| File | Change |
|---|---|
| apps/desktop/src/Well3DWorkspace.tsx | Saved-coordinate scene, disclosure, shared selection and measurement |
| apps/desktop/src/DirectionalWorkspace.tsx | Accessible plot-point selection in both directions |
| apps/desktop/src/main.tsx | Original survey-station MDs bound only to the matching source |
| package.json / pnpm-lock.yaml / pnpm-workspace.yaml | Pinned scene dependencies and scene check command |
| .github/workflows/ci.yml / release.yml | Require type/scene checks on both CI platforms and releases |
| tools/build_streamlit.py | Reproducible LF line endings for generated SVG copies |
| apps/streamlit/component/index.html / manifest.json | Current source fingerprint and verified compiled assets |
| GEODRILL_PRO_V0.9_PROGRESS.md / docs/V09-ARCHITECTURE-AUDIT.md | Evidence-based current status and remaining architecture |
| ../WORKSPACE-STATUS.md | Current Project Drill checkout and distribution status |

## Files Deleted / Retired

| File | Reason |
|---|---|
| apps/streamlit/component/assets/index-PgqFzM0o.js | Superseded generated asset; previous Git/release baseline remains preserved |

No user project, raw data, release candidate or historical evidence was deleted.

## Architecture Decisions

Saved kernel geometry remains authoritative. Three axes are +X East, +Y elevation and -Z North. Subtract the reference origin in double precision before storing Float32 buffers. Display scaling/exaggeration never modifies canonical input or engineering results. Do not render mismatched frames or inconsistent saved reference coordinates. Missing WebGL is disclosed; coordinates remain accessible.

## Dependencies Added / Removed

| Dependency | Change | Reason |
|---|---|---|
| three 0.186.1 | Added | Renderer |
| @react-three/fiber 9.8.1 | Added | React 19 renderer |
| @react-three/drei 10.7.9 | Added | Orbit controls |
| @types/three 0.186.0 | Added (development) | Type validation |
No existing runtime versions removed.

## Database / Schema Changes

None. Verification uses isolated synthetic data under build/scene-check-data. Original application/user data remain untouched.

## API Changes

None. The view consumes preserved saved geometry and existing survey data. Backend scene-cohort contracts and reference-bound entities remain open.

## Engineering Kernel Changes

None. No survey integration, coordinate conversion, covariance propagation or clearance computation is introduced in the renderer.

## UI / UX Changes

Lazy real WebGL workspace and shared saved-depth selection. Plan markers expose mouse, Enter and Space selection with pressed state. Canonical metre values, source hash, frame/datum/north and historical-source disclosure remain visible. The 100-row sample window is bounded; it is not a full virtualized engineering grid.

## Branding Changes

Existing palette and brand retained. Version still inherits alpha.2 while this isolated development branch is unfinished; it is not a new released alpha.2 build.

## 3D Changes

Real WebGL trajectory consumes saved kernel samples. Layer groups include WellsGroup and GeologicalGroup. Formation patches are explicitly illustrative interpreted planes, not regional surveyed surfaces. Casing centre lines do not model physical diameters. Full phase 5 remains open.

## Realtime Changes

None.

## Tests Run

| Command | Result | Notes |
|---|---|---|
| node tools/test_scene.mjs | 23 passed | Includes actual Three.js raycast identity, offset/scroll/DPR guards, invalid frames and 100k-sample data processing |
| node node_modules/typescript/bin/tsc -b | Passed | Changed scene and SVG interaction types |
| Python tools/build.py | Passed | Selected immutable release-ef017ebc0dae4c329c20d51d285decaa |
| Python tools/build_streamlit.py | Passed | Complete component and current source fingerprint |
| python -m pytest -q --basetemp build/pytest-scene-picking-20261009 | 697 passed | 268.85 seconds; one existing Starlette/httpx deprecation warning |
| YAML parse of ci.yml and release.yml | Passed | Scene checks now required in the workflows |

No new scene Windows binary or independent field qualification is established by these tests.

## Test Summary

697 Python tests and 23 separate scene checks passed. The scene checks cover numerical geometry, reference identity and an actual Three.js Points raycast. The 100k-sample check processes data; it does not establish representative WebGL interaction performance. The prior candidate CI is historical evidence; this changed source has not yet run remotely.

## Manual Verification

- Standalone saved synthetic revision ca53b9e0 rendered with WebGL ready.
- A real canvas click changed MD 0 to MD 500; selected N 43.733, E 23.891, TVD 496.673 metres matched the saved sample.
- 3D to directional: source table row and plan marker showed MD 500.
- Directional to 3D: keyboard plot selection set MD 1000, N 130.907, E 71.515, TVD 986.707 metres.
- With feet and vertical exaggeration x2, another actual canvas click restored MD 1000 and retained the same canonical coordinates.
- Canonical straight-line distance from saved MD 500 to 1000 remained 500.000 metres.
- Local Streamlit at 8888 rendered its real lazy WebGL chunk. Inside the iframe, a real click changed MD 0 to 500 with saved N/E 0 and TVD 500 metres in the explicitly synthetic vertical fixture.
- Public Streamlit was asleep, then awakened and visibly showed Version 0.9.0-alpha.1.
- GitHub PR #2 is merged, research-6 published, PR #4 remains open at b53757b.
- Original candidate checkout is clean; its alpha.2 release manifest and binary hashes remain unchanged.

## Current Working Tree

Uncommitted v09-engineering-scene development based on b53757b. Original geodrill-pro candidate is clean. The isolated services currently running are the owned 8877 workstation and 8888 Streamlit host; stop only their exact owned processes after acceptance. Port 8765 belongs to another application and must remain untouched.

## Known Issues

- Full phase 5 remains incomplete: saved role/offset cohorts, targets/BHA, covariance meshes, exact closest-approach overlays, clipping/section controls and representative interactive load.
- Lazy renderer is 947.50 kB / 255.93 kB gzip; Vite size warning and upstream THREE.Clock deprecation remain.
- Local distribution guards and actual Streamlit WebGL pass; the public app remains alpha.1 and no Windows binary has been rebuilt for the scene.
- Default desktop/source launch uses port 8765, currently occupied by another app. Add a bounded explicit loopback-port option and prove ownership/collision behavior before packaged runtime acceptance.
- PR #4 publication decision remains pending separately.

## Incomplete Work

All remaining phase-5 requirements listed in docs/V09-ENGINEERING-SCENE.md, plus regression/cloud/Windows/release acceptance. The complete architecture remains unfinished.

## Important Do Not Break Items

- Original bytes, immutable revisions/reports and wellbore/role ownership.
- Shared selection must reference the displayed saved revision; historical inspection must not activate it.
- No implicit CRS conversion, field accuracy claim, fabricated covariance mesh or clearance.
- equipment_control=false and equipment_authority=none.
- Keep PR #4/research-6 and their exact release evidence separate from this development work.

## Next Session — Start Here

Work is active. If interrupted, query usage and inspect this isolated checkout before continuing. Canvas raycast and primary plot/table/3D synchronization are now verified; do not repeat the old failed gate as current. Next finish explicit loopback-port ownership and packaged scene acceptance, then source-bound role/offset cohorts. Use the original geodrill-pro .venv interpreter with cwd kept in this isolated checkout. Services require normal loopback permissions; the unrelated application on 8765 is not ours.

## Next 3 Priorities

1. Finish isolated desktop runtime acceptance on a chosen loopback port, including collision/ownership guards and scene artifact identity.
2. Connect saved planned/actual/scenario/offset geometry and exact diagnostics without inferred reference transformations or fabricated covariance.
3. Finish remaining phase-5 interactions/performance/recovery gates; separately complete alpha.2 publication only after its pending approval.

## Acceptance Criteria Still Open

The complete matrix in docs/V09-ENGINEERING-SCENE.md remains authoritative. Primary saved-source point picking and plot/table/3D synchronization are verified. Role/offset entity synchronization, the complete scene graph, clipping/section controls, covariance axes, exact closest-approach geometry, representative interactive load, recovery and scene Windows/release acceptance remain open.

## Deferred Work

Docking/themes, Tauri/update/rollback, enterprise services, authorized live-provider acceptance and independent engineering/security qualification remain subsequent full-architecture gates.

## Source / Evidence Notes

Supplied master prompt, architecture and exact 29-section template are requirements; another AI's progress is reported evidence. Base b53757b, changed source currently uncommitted. Actual saved synthetic fixtures were used only for software verification. Official event/raycast references: https://r3f.docs.pmnd.rs/api/events and https://threejs.org/docs/pages/Raycaster.html. GitHub/live runtime were rechecked on 9 October. Scene proof: docs/evidence/v09-scene-raycast.jpg. Historical candidate bytes: docs/evidence/v09-alpha2-handoff-from-b537.md.

## Handoff Summary

The critical actual raycast and bidirectional primary-depth repair is complete and verified in the standalone and Streamlit workstations. 697 Python tests, 23 scene checks, TypeScript and production assets pass. The full architecture and phase 5 remain open. Continue from desktop port/runtime acceptance and saved cohort integration; preserve the original candidate and published alpha.1 baseline.
