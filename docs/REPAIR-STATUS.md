# GeoDrill repair status — 6 October 2026

Implemented and verified:

- Declared missing cryptography, directional and protocol runtime dependencies.
- Isolated pytest temporary directories; full regression passes 577 tests.
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
- Reconciled commercial gate claims and recorded current internal security checks.

Artifacts in this checkout:

- dist/GeoDrillPro-Setup.exe: unsigned research installer.
- dist/GeoDrillPro-Windows-x64.zip: unsigned portable package.
- dist/SHA256SUMS.txt and dist/release-manifest.json: integrity and signing state.
- docs/evidence/repair-verification.json: current verification results.
- docs/evidence/windows-installer-verification.json: installation and recovery checks.
- docs/evidence/SOURCE-PROVENANCE.md: original-source acquisition and remaining observations.

Required external steps:

1. Review and merge the repair pull request. Direct main-branch publication was rejected by automatic approval review. Then verify the final Streamlit build and a representative rendered interaction.
2. Supply/configure a trusted publisher signing certificate for a signed release. This is distinct from the working unsigned research installer.
3. Complete original-source model validation for remaining field/experimental claims and obtain a named independent engineer's scope-specific signed review.
4. Obtain an actual external security assessment and organizational certification evidence before making compliance claims.

The goal remains open while those requirements are missing. Equipment control and automated drilling clearance remain false.

See [release and independent-review handoff](RELEASE-AND-QUALIFICATION-HANDOFF.md) for the concrete remaining inputs and acceptance evidence.
