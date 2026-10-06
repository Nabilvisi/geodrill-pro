# GeoDrill repair status — 6 October 2026

The approved repair PR is merged. The latest verified publication is unsigned
research-5 at source 77e3e91885b9994f6ed0eedee85bb7567e6738f6, with 635 passing
tests and actual downloaded-package workflow verification. Current evidence is
[geomechanics-verification.json](evidence/geomechanics-verification.json).
The following repair milestone records the earlier research-2 release; later dated
increments appear below.

- Live app: https://geodrill-pro.streamlit.app/
- Earlier repair prerelease: https://github.com/Nabilvisi/geodrill-pro/releases/tag/research-2
- Earlier repair code: b213c1f861ea508590886751ea9febcee2c27656
- Windows/Linux CI: https://github.com/Nabilvisi/geodrill-pro/actions/runs/37444825114
- Release workflow: https://github.com/Nabilvisi/geodrill-pro/actions/runs/37444938024
- Earlier repair evidence: docs/evidence/published-research-verification.json

Implemented and verified:

- Declared missing cryptography, directional and protocol runtime dependencies.
- Isolated pytest temporary directories; the original local repair regression passed 577 tests. Final Windows and Linux CI each pass 578 tests, including native cloud report export preservation.
- Removed automatic field qualification and invented independent sign-off.
- Direct benchmark calls withhold independent validation and leave unverified source licenses unset.
- Survey comparisons reject reflected coordinate vectors even when radial displacement agrees.
- Corrected the failed FORGE axial-band comparison and withheld circular friction validation.
- Added original-source FORGE trajectory reproduction across all 422 stations with source hashing and corruption rejection.
- Rebuilt current desktop and Streamlit frontend assets.
- Rebuilt the standalone executable with welleng model data and directional fixtures.
- Verified the packaged API and all three bundled directional diagnostics.
- Built the missing Windows installer; isolated install, execution and uninstall pass.
- Confirmed uninstall preserves extra user-created files and persistent evidence.
- Verified ZIP/executable identity, generated final hashes and explicit unsigned release manifest.
- Added a bundled source-file snapshot and rejection of source changes after packaging.
- Added manifest-bound installer recovery checks to the release workflow.
- Repaired the release pipeline to test/build current source, sign before ZIP creation, require trusted publisher certificates, and withhold unmatched assets.
- Replaced dead hosted download links with actual release-asset discovery and truthful unavailable states.
- Rebuilt the Streamlit dependency environment and verified the rendered synthetic project, all 240 telemetry records, charts and hydraulics navigation.
- Added a native cloud report download alongside the embedded export. Downloaded the actual complete JSON and verified its canonical snapshot fingerprint.
- Published research-2 after regression, packaged diagnostics, installer execution/recovery and artifact identity checks. Downloaded both public Windows packages and confirmed their exact manifest hashes.
- Verified the live app links to the actual research-2 installer, portable ZIP and checksums.
- Reconciled commercial gate claims and recorded current internal security checks.

Artifacts in this checkout:

- build/published-research-2/: downloaded final public installer, portable ZIP, manifest, checksums and verification evidence.
- build/published-research-2/live-app.jpg and live-downloads.jpg: rendered deployment evidence.
- The older dist root artifacts below record the earlier local research build; the final published files are in build/published-research-2 and the linked GitHub prerelease.

- dist/GeoDrillPro-Setup.exe: unsigned research installer.
- dist/GeoDrillPro-Windows-x64.zip: unsigned portable package.
- dist/SHA256SUMS.txt and dist/release-manifest.json: integrity and signing state.
- docs/evidence/repair-verification.json: current verification results.
- docs/evidence/windows-installer-verification.json: installation and recovery checks.
- docs/evidence/SOURCE-PROVENANCE.md: original-source acquisition and remaining observations.

Required external steps:

1. Supply/configure a trusted publisher signing certificate for a signed release. This is distinct from the verified unsigned research prerelease.
2. Complete original-source model validation for remaining field/experimental claims and obtain a named independent engineer's scope-specific signed review.
3. Obtain an actual external security assessment and organizational certification evidence before making compliance claims.

The merge, hosted repair and unsigned research publication are complete. Full independent qualification and trusted publisher distribution remain open while the external requirements are missing. Equipment control and automated drilling clearance remain false.

See [release and independent-review handoff](RELEASE-AND-QUALIFICATION-HANDOFF.md) for the concrete remaining inputs and acceptance evidence.

## Completion audit and subsequent recovery repair

The broader code audit found remaining software scope beyond the three external gates:
ETP/WITSML streaming is absent; automatic update/binary rollback is absent; several
advanced capabilities have only API/kernel paths, and broader hydraulic/contact
closures remain unsupported. These are unfinished requirements. The former statement
that only external qualification remained is superseded by IMPROVEMENT-PLAN.md.

Subsequent recovery source passes 602 tests locally. It adds atomic failed migrations,
whole-workstation backup/restore, explicit imported-study audit records, signature/key
preservation through re-export, archive/identity validation and packaged recovery
arguments. See evidence/recovery-verification.json and GD-A08-IMPLEMENTATION.md.
Research-2 remains the verified earlier publication; these changes require their own
CI and packaged-release acceptance before a newer binary is claimed.

## Published recovery and connected workflow continuation — 6 October 2026

Research-3 at c4037d21ed3313ef21a335882a1330b24f00c41e passed 602 tests on both Windows and Ubuntu and in its release job. Actual installed-EXE backup, wrong-hash refusal, fresh restore, existing-destination preservation, signing-key preservation, restored API diagnostics, install and uninstall passed. Full downloaded public installer/ZIP bytes match the release hashes. See [published recovery evidence](evidence/published-recovery-verification.json).

The subsequent offset benchmarking and evidence search integration is described in GD-A14-IMPLEMENTATION.md and GD-A18-IMPLEMENTATION.md. These are separate from research-3 binaries until a newer package is verified. ETP/WITSML streaming, automatic update/binary rollback, dedicated team/directional/geomechanics integration, wider model closures and external qualification remain unfinished.



## Published connected workflows — 6 October 2026

Research-4 at e03d35c510d369759961c374def0928147442364 is published. All 615 tests passed locally, on Windows/Ubuntu CI and in the Windows release job. The hosted app was restarted and verified through saved offset-study reopening, a new study saved through the UI, three source/calculation citations, cited-record inspection, changed-query clearing and no-match abstention. The served frontend JavaScript bytes match the recorded hash.

Actual installed-EXE backup/restore, wrong-hash rejection, existing-destination preservation, signer preservation, restored diagnostics, install and uninstall passed again. All four full public downloads match their hashes, and the portable EXE and canonical source-snapshot digest match the manifest. The installer is unsigned (NotSigned); independent engineering qualification and external security assessment remain pending. See [current evidence](evidence/connected-increments-verification.json), [release](https://github.com/Nabilvisi/geodrill-pro/releases/tag/research-4), [offset implementation](GD-A14-IMPLEMENTATION.md) and [evidence search implementation](GD-A18-IMPLEMENTATION.md).

This closes this increment's source, hosted and package checks. Read-only ETP/WITSML streaming, automatic update/binary rollback, dedicated team/directional/geomechanics integration, broader qualified model closures and representative operator acceptance remain open in [the delivery matrix](IMPROVEMENT-PLAN.md).



## 6 October 2026 — published geomechanics increment (research-5)

Source 77e3e91885b9994f6ed0eedee85bb7567e6738f6 repairs the survey-bound MC/Mogi geomechanics model and connects original-input preservation, editable core/closure records, saved studies, citations and fixed reports. Local regression, Windows/Ubuntu CI 37461989646 and release workflow 37462177431 each passed 635 tests. The live app rendered 27 workspace pages and eight seeded research workflows; complete and missing-core withheld cases were saved and reopened, and the complete citation inspected.

All four complete research-5 downloads matched their published SHA-256 hashes. ZIP CRC, bundled executable and source-snapshot digest were verified. The actual downloaded portable executable passed HTTP import, original-hash/geometry binding, complete and withheld calculations, saved-record citation and fixed-report checks against an isolated data directory. Installer install/execute/backup/restore/uninstall acceptance passed, including wrong-hash and existing-destination refusal and user evidence preservation. Signing remains explicitly unsigned.

Current release: https://github.com/Nabilvisi/geodrill-pro/releases/tag/research-5
Live app: https://geodrill-pro.streamlit.app/
Evidence: docs/evidence/geomechanics-verification.json
Scope: docs/GD-A17-IMPLEMENTATION.md

Actual characterized-fluid and coupled thermal/poroelastic or multiphase experiments, read-only ETP/WITSML, updater/rollback, dedicated team/directional UI and broader original model acceptance remain open. Publisher signing requires the owner's certificate; original engineering observations and independent engineering/security assessments remain external prerequisites. Equipment control and drilling clearance remain unavailable. Earlier release entries retain their dated historical scope.
