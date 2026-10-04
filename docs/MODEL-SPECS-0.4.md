# Module 5 — imported EM vendor result review / version 0.4.0

This implements audit Part 1 section 5.5's MVP scope: display imported vendor interpretations with provenance. No Maxwell forward response, native EM inversion, alternative-earth-model search, boundary-surface construction, geosteering execution or engineering approval is implemented.

## Interchange and evidence

The endpoint accepts UTF-8 JSON with schema_version "geodrill-em-vendor-1"; examples are in docs/examples/synthetic-em-vendor.json and available from the workstation. Imports are bounded to 2 MiB and 1,000 strictly increasing native-MD samples. Repeated passes require separate files. Origin, exact well name and declared MD datum must match the project. Synthetic examples cannot be imported into historical projects.

Required document metadata: origin; source and data-rights notes; tool vendor/name and processing version; declared frequencies and antenna spacings (empty lists explicitly mean absent); orientation/geometry evidence; optional tool-to-bit spacing; dimensionality; forward-model reference; calibration/environment, prior/regularization and uncertainty/nonuniqueness notes; optional supplied qualification reference.

These references are supplied text. A nonempty reference is not proof of access, licensing, instrument qualification, correct calibration or model validation. The integration-readiness panel separates supplied facts from independently unverified raw measurement, forward model and inversion benchmark interfaces. Native inversion remains unavailable even if all supplied metadata fields are populated.

Samples preserve acquisition and optional receipt timestamps with explicit UTC offsets; horizontal and vertical resistivity in exact ohm.m units; optional signed boundary distance in m; supplied parameter intervals with their stated meaning; vendor quality and its note; optional nonnegative misfit with statistic/normalization definition. Boundary distances require a reference point, direction and sign convention. There is no assumed correspondence between a scalar signed distance and an actual 3D surface.

Positive resistivity and containing positive intervals are required. Interval ordering and numerical envelopes are validated; malformed values are rejected at import rather than clipped. Missing estimates/intervals remain null. Vendor_usable, vendor_rejected and unknown are accepted quality labels; no supplied label is promoted to GeoDrill approval.

Original uploaded bytes, their SHA-256, normalized Parquet and its SHA-256 are preserved. Review validates both files, project ownership, source/project identity and the immutable M1 geometry source. It binds raw, Parquet and geometry hashes into the saved calculation. Historical saved results are reproducible evidence snapshots rather than an assertion that the source remains operationally suitable today.

## Arithmetic and applicability

Aligned_MD = native_MD + explicitly supplied MD_offset.

This is an alignment within the same declared datum. The offset cannot authorize a datum transformation. Tool-to-bit separation is preserved separately and never subtracted, added or inferred automatically. No interpolation, resampling or spatial boundary projection is performed.

Receipt_delay_s = receipt_timestamp - acquisition_timestamp, using the supplied UTC offsets. A receipt preceding acquisition is invalid. A missing receipt produces null delay. This arithmetic is not a telemetry latency guarantee, solver duration, live freshness model, tool cadence or a complete arrival-time reconstruction.

A sample is displayed only when all these conditions hold:

- Review declares supplied alignment confirmed.
- Aligned MD lies within the saved survey's measured-depth extent.
- Vendor quality is vendor_usable.
- At least one interpreted resistivity or boundary distance is present.

Otherwise the display is null, with explicit reasons; all supplied values remain accessible in the evidence table and report. Unknown alignment withholds every sample. Geometry/source/offset/datum changes reset the relevant UI alignment confirmation. Changing import/source also clears source-specific evidence notes.

Scatter plots retain native spacing and show eligible Rh or boundary points with supplied interval bars. Missing and withheld observations are never joined. Rv remains in the table and complete source evidence. The first 100 observations are displayed in the table; the saved result/report retains all allowed observations. Interval meanings are preserved, with no replacement by a default confidence level. Missing resistivity interval count means a displayed sample has at least one supplied resistivity component without its associated interval.

## Verification and limits

Thirty new tests cover native-value preservation, eligibility and uncertainty absence, mixed UTC-offset arithmetic, aligned MD without altering boundaries/tool spacing, datum/extent gates, malformed intervals/timestamps/units/order/tool values, supplied versus verified qualification, upload identity/type, duplicates, project isolation, raw/Parquet corruption, immutable calculation rows, restart and fixed-report inclusion.

Chrome verifies synthetic 5/8 displayed, unverified-alignment 0/8 displayed, actual JSON upload/duplicate preservation and evidence reset, saved studies after a full reload, report source/model inclusion and a 390 px layout without document overflow.

No vendor API adapter or proprietary native format is claimed. A real integration still requires the selected vendor/tool, actual calibrated channels, frequencies and geometry, accessible qualified forward model, noise/environment/priors, independent benchmarks, blind uncertainty checks and specialist review.

## Source context

The software follows the already reviewed local audit. Current vendor primary material reinforces the need to preserve instrument-specific frequency/spacing/antenna and uncertainty information; it is context, not validation of this implementation:

- Halliburton StrataStar: https://www.halliburton.com/en/products/stratastar-service
- SLB triaxial measurement/inversion technical paper: https://www.slb.com/resource-library/technical-paper/dr/spwla-2026-0139

Marketing distance/performance claims from those sources are not adopted as acceptance criteria.
