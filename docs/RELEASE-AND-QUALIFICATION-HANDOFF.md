# Release and independent-review handoff

The tested repair is [pull request 1](https://github.com/Nabilvisi/geodrill-pro/pull/1).
The user approved merge, deployment and unsigned research publication on 6 October 2026.
PR 1 is merged at 509be9b9a96fda0604be2ce1eda205e9ea691280. A follow-up native
cloud report export repair is published at b213c1f861ea508590886751ea9febcee2c27656.

## Research deployment

Completed: final Windows/Linux CI each passed 578 tests; the Streamlit environment
was rebuilt and https://geodrill-pro.streamlit.app/ renders the title, synthetic
demonstration project, 240 telemetry records, charts and module navigation. The
actual complete report was downloaded using the native cloud control and its
canonical snapshot hash verified. Current evidence is in
docs/evidence/published-research-verification.json.

Completed: https://github.com/Nabilvisi/geodrill-pro/releases/tag/research-2
was built with the explicit unsigned research input. Release workflow
37444938024 passed regression, rebuilt the frontend and executable, exercised
packaged diagnostics, compiled the installer, verified source/artifact identity,
and passed install/run/uninstall recovery before publication. Both public Windows
downloads match their manifest hashes; the live app links to those actual files.

The final downloaded public packages are under build/published-research-2; dist
also retains the earlier local research packages. Their manifests declare
the actual signing state. SOURCE-SNAPSHOT.json records individual source-file hashes
and a combined digest, including uncommitted source. The verifier rejects source
changes made after packaging. Generated verification reports are outside that digest.

## Publisher-signed distribution

A trusted publisher certificate must be supplied by its owner. The workflow expects
the CODESIGN_PFX_BASE64 and CODESIGN_PASSWORD GitHub Actions secrets. Configure
these through GitHub's secret interface; do not commit or paste the private key or
password into this repository. Tagged releases require signing and trusted Windows
verification of both the executable and installer. An unsigned research prerelease
does not close this requirement. Generated/self-signed development certificates are
not accepted as publisher evidence.

## Independent engineering review

Start from docs/evidence/SOURCE-PROVENANCE.md, the original FORGE workbook and
its 422-station residual report, and the provisional field dossier. Supply the
missing original Volve records, native vibration observations, flow-loop experiments
and instrumented force/torque data before attempting the corresponding validation.

For every reviewed case, preserve raw file hashes and license, exact extraction
locations, unit/depth/coordinate/time references, instrument quality and uncertainty,
complete geometry, production model/version, declared applicability and tolerance,
calibration-only data and distinct holdout records, all residuals and exclusions.
The reviewer must provide their own identity, scope, findings and signed assessment.
Numeric agreement, sample fixtures and internally generated reports cannot supply it.

## Independent security review

The current security report records internal checks and their scope. An external
assessor must define and execute their assessment, review authentication and project
authorization, evidence/signing trust, import/archive boundaries and operational
deployment, then supply actual findings and assessment evidence. Organizational
SOC 2/ISO certification requires its own valid evidence; passing tests and scanners
does not establish it.

Equipment control and automated drilling clearance remain unavailable throughout
these release and review steps.

## Additional software scope found by the completion audit

The current IMPROVEMENT-PLAN.md supersedes the earlier implication that only external
review/signing remained. Read-only ETP/WITSML streaming, automatic update/binary
rollback, dedicated workflows for API/kernel-only increments and broader validated
hydraulic/contact/transient closures remain unfinished. Original backlog acceptance
criteria are retained. The new recovery repair has separate source evidence in
recovery-verification.json and must pass its own packaged release checks.

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
