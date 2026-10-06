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
