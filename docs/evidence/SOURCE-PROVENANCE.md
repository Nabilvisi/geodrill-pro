# Original-source acquisition and benchmark provenance

Acquisition date: 6 October 2026.

## Utah FORGE survey — acquired and reproduced

Source: [GDR submission 1283](https://gdr.openei.org/submissions/1283),
[DOI 10.15121/1776602](https://doi.org/10.15121/1776602).
Dataset attribution: McLennan, John, University of Utah Energy and Geoscience Institute,
Utah FORGE: Well 16A(78)-32 Drilling Data, 2021. The GDR record declares CC BY 4.0.

The original [survey workbook](https://gdr.openei.org/files/1283/16A%2878%29-32%20Survey.xlsx)
is retained unchanged at `sources/forge-16a-survey.xlsx`.
SHA-256: `ad03773329769f702f748c96244a9e1cba16cd1d762d4e8b93b8c8fea9d36b8d`.

Extraction: Sheet1, rows 77–498, all 422 stations. C = MD, D = inclination,
E = azimuth, G = TVD, I = north displacement, J = east displacement.
Length conversion is US survey foot, explicitly declared as usft in the report,
using 1200/3937 m. Angular values are degrees. Raw XML numeric values are read
because the source workbook formats some numerical cells as dates.

`python tools/verify_forge_survey.py` calls the production minimum-curvature kernel.
The predeclared 1 m absolute 3D tolerance accommodates cumulative published angle
rounding at 0.01 degrees. All 422 coordinate comparisons pass with a maximum
3D difference of 0.00255731 m, with no station exclusions. Full residuals are in
`forge-survey-verification.json`. A modified source file is rejected before parsing.
This reproduces published calculations; it does not validate survey accuracy,
tool uncertainty, BHA dynamics, ECD, alarms or operational engineering authority.

## Remaining independent observations

| Claimed benchmark | Current evidence | What is still required |
|---|---|---|
| Volve trajectory and DDR ECD | Embedded numbers only; no original extraction verified | Original survey/DDR records, dates and unit/reference mapping, license and raw file hashes |
| FORGE torsion and axial bounce | Original survey acquired; dynamics numbers remain unverified | Native downhole records and instrument metadata, PSD/mode extraction, applicability and held-out comparisons |
| Tulsa cuttings flow-loop | Embedded example fits its own targets | Original experiment/paper tables, rheology/geometry/rotation conditions, production-model comparisons |
| Instrumented downhole friction | Previous circular arithmetic withdrawn | Original survey/string/forces, calibration-only fit and separate holdout observations |

The [Equinor Volve source portal](https://www.equinor.com/energy/volve-data-sharing)
publishes its own Open Data Licence; the former blanket CC BY 4.0 assignment
to unverified embedded Volve values is withdrawn. Named independent reviewers
and scope-specific signed assessments have not been supplied.

The [FORGE dynamics source review](FORGE-DYNAMICS-SOURCE-REVIEW.md) records
sampling and processed-data limitations from primary sources, plus the verified
Larsen article identity. These sources do not establish the embedded vibration
targets or Tulsa observations. Direct benchmark calls now include the same
withheld validation status and absent license as the suite.
