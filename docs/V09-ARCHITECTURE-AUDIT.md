# GeoDrill Pro v0.9 architecture verification — 7 October 2026

The supplied implementation report is not sufficient to establish v0.9 completion. Its original bytes are retained in [the reported progress](evidence/v09-reported-progress-20261007.md). This audit uses the implementation master prompt, full-stack architecture and progress template supplied by the user. The architecture remains the target; interim repairs below do not replace its acceptance criteria.

## Baseline and discrepancies

The starting local and GitHub main revision was `3268a82d36699c00fbd126fb4d8d791f8d6dd7f5`. The clean baseline independently passed **668 tests** in 231.04 seconds. The GitHub CI run for that revision had succeeded. That establishes regression evidence, not independent field qualification.

The Streamlit wrapper displayed a v0.9 caption while shipping a component manifest at 0.8.0 and the previous embedded navigation. The local Windows manifest also identified an earlier 0.8.0 build. Consequently the supplied claim that every distribution was current was incorrect.

The new directional page generated uncertainty ellipses and safe offset results from browser constants, while the new 3D page used a fixed demonstration trajectory. Those values were not bound to saved calculation evidence. New v1 project/well/wellbore paths bypassed existing project membership checks. Torque/drag and geomechanics v1 routes did not correctly use the preserved geometry/source calculation gates. The workstation header invented a selected wellbore, plan, coordinate reference and verification status.

## Repaired preview

The application is labelled **0.9.0-alpha.1**, an engineering research workstation preview. Existing engineering equations and model versions remain distinct from the application version.

- Streamlit embeds the rebuilt React application. Its startup guard verifies the version, normalized frontend source fingerprint, contained asset paths and every asset hash. A changed source or corrupt/stale component fails explicitly.
- Directional tables and plan coordinates use the actual imported survey and saved minimum-curvature result. Uncertainty calls the preserved Python kernel; absent latitude, magnetic field and dip metadata produce a withheld result. No browser-generated offset clearance is presented.
- The interim spatial viewer uses the saved geometry samples, declared formations/casings and shared selected MD. It discloses its SVG projection and source revision. It is not the specified Three.js/R3F subsystem. Historical geometry and late uncertainty results cannot silently become current after a survey change.
- The project tree supports persisted field, well, wellbore and target creation with explicit inputs. Foreign field and sidetrack-parent associations are rejected. Surveys remain in the legacy project scope; the tree does not yet establish complete wellbore-specific revision ownership.
- The v1 project list and nested resources now use project membership authorization in team mode. Torque/drag and geomechanics resolve the wellbore's owning project and use the existing immutable input, geometry, evidence, calculation-save and report paths.
- Context headers show the actual saved revision and declared/unknown references. Research, withheld and stale states are not replaced with a generic verified badge. The approved blue/teal palette is applied to the refreshed shell, with native CSS replacing unconfigured Tailwind classes in repaired pages.
- Windows preview packaging keeps the prior bundle and records exact source bytes. A dedicated `v09-verified-release` branch can trigger an unsigned prerelease using the existing regression, smoke, archive, installer and recovery checks. Version tags continue to require trusted publisher signing.

## Architecture acceptance matrix

| Phase | Current evidence | Status and acceptance still open |
|---|---|---|
| 0 — Baseline freeze | Clean 3268a82 retained in Git; 668-test local rerun; previous bundle retained on rebuild; original report archived | Baseline observed. This is not a newly signed v0.8 freeze release or a clean-machine qualification. |
| 1 — Architecture refactor | Domain envelopes, application services, modular v1 routers and preserved kernel/API paths exist | Partial. `services/api/main.py` still carries legacy research/application logic; uniform stable errors and complete dependency graph remain open. |
| 2 — Design system and shell | Brand assets, feature navigation, contextual header, command palette, repaired blue/teal styling | Partial. Docking, persisted panel layouts, complete light/dark themes, density modes and broad keyboard/accessibility acceptance remain open. |
| 3 — Project/well domain | SQLite migration/hierarchy, persisted CRUD tree, membership checks and cross-parent rejection tests | Partial. Per-wellbore survey/trajectory revision migration, edit workflows, and tree-driven complete engineering context remain open. |
| 4 — Directional flagship | Source-backed survey and minimum-curvature coordinates; uncertainty/proximity/geodesy kernels; metadata withholding; shared MD | Partial. Complete planned/actual wellbore workflow, integrated offset selection/proximity UI, synchronized depth plots and field/tool-specialist review remain open. |
| 5 — 3D workspace | Interim saved-kernel SVG projection, source/datum disclosure, casing/formation layers and selected-station coordinates | Incomplete. No Three.js/R3F dependency, full scene graph, uncertainty/collision meshes, all entity picking, WebGL load/performance acceptance or BHA/target/offset scene integration. |
| 6 — Engineering workspaces | Existing source → saved geometry → research calculation → immutable report paths retained; repaired v1 torque/drag and geomechanics integration | Partial. Common case selection/comparison across all new workspaces and full wellbore revision ownership remain open. Existing model-specific limitations still apply. |
| 7 — Realtime foundation | Read-only capture/client/replay and quality infrastructure with deterministic fixture tests | Partial. Existing lab implementation does not establish authorized live provider interoperability, all WITSML objects, field latency or uninterrupted reconnect under representative conditions. |
| 8 — Desktop | Existing PyInstaller/FastAPI launcher, source snapshots, portable ZIP, Inno installer and recovery checks | Legacy research distribution. Tauri managed sidecar, trusted signing, automatic updater, binary rollback and independent clean-machine operator acceptance remain open. |
| 9 — Enterprise | Local team roles, membership/audit controls and new v1 isolation tests | Incomplete. PostgreSQL/PostGIS/Timescale, object storage, OIDC, production tenancy/monitoring and external security review are not delivered by the local team API. |
| 10 — Qualification | Preserved synthetic/published diagnostic and numerical regression infrastructure | Incomplete. Model-specific authorized datasets, original observations, residual/holdout evidence, independent review and field acceptance remain open. |

## Evidence and practical limits

[The progress record](../GEODRILL_PRO_V0.9_PROGRESS.md) follows the supplied template and records final commands, local/remote revisions, package hashes and manual verification. [Machine-readable verification](evidence/v09-verification.json) separates local tests, local packages, GitHub builds and rendered Streamlit evidence. Historical release records are retained with their original revision identities.

The source guard is portable across LF/CRLF checkouts, while Windows `SOURCE-SNAPSHOT.json` deliberately hashes the actual packaged bytes. Different release runners can produce different binary hashes; verify against the manifest for the package actually downloaded.

Passing tests, an executable smoke run, a spatial rendering or a successful deployment do not establish engineering or security qualification. `equipment_control=false`, `equipment_authority=none`, and no automated drilling clearance remain enforced boundaries.

## Next implementation gates

1. Finish the wellbore-owned survey/trajectory/revision migration and complete directional uncertainty/proximity workflow with source staleness and fixed report acceptance.
2. Implement the architecture's Three.js/R3F scene and synchronized grid/plots, then validate coordinates, picking, covariance axes and representative load. Introduce docking/themes without altering calculation authority.
3. Complete Tauri/update/rollback and the intended enterprise stack as separately verified increments, followed by model-specific independent qualification and external security review.
