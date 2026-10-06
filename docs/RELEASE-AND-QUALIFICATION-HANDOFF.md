# Release and independent-review handoff

The tested repair is [pull request 1](https://github.com/Nabilvisi/geodrill-pro/pull/1).
Merge approval is pending. No direct update to the default branch is authorized.

## Research deployment

After approval, merge the current tested PR head, wait for its final Windows/Linux
CI results, and observe the Streamlit dependency build at
https://geodrill-pro.streamlit.app/. Verify the rendered title, a demonstration
project, charts, navigation and report download. A successful repository merge or
dependency installation alone does not establish a working hosted deployment.

Use the Release workflow's explicit unsigned research input for a prerelease.
The workflow must run regression, rebuild the frontend and executable, exercise
packaged diagnostics, compile the installer, verify source/artifact identity,
install/run/uninstall it, and preserve the verification artifacts before publishing.
Confirm the published installer/ZIP hashes and the app's actual download links.

Local research packages are already available under dist. Their manifests declare
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
