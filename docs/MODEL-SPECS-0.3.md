# M4 research model specification — version 0.3.0

## Selected construction and source

The implementation uses the defined Thomas-Stieber wet-shale/primary-pore volume construction, not the apparent-sonic model discussed in the earlier source review. The published background construction describes clean, dispersed-filled, structural-replacement and pure-shale vertices in effective-porosity coordinates and explicitly identifies coexisting textures as a source of nonuniqueness.

Reference: Christopher Hugh Skelt, published specification AU2013315927B2, background paragraphs 0008–0011 and Figure 3, https://patents.google.com/patent/AU2013315927B2/en. Numerical source vertices at sand porosity 0.3 are M=(0,0.3), D=(0.3,0), S=(0.7,0.3), Z=(1,0), with coordinates (bulk shale, primary porosity).

The implementation does not solve a joint mineral/fluid log-response inversion or assert a patent licence. Independent petrophysical review and compatible field evidence remain open.

## Explicit volumetric definitions

All volumes below are fractions of bulk rock. Let a be clean-sand framework porosity, b be wet-shale endmember porosity, L laminated wet-shale bulk volume, D dispersed wet-shale bulk volume, S structural wet-shale bulk volume, v observed/interpreted total wet-shale volume and t supplied total physical porosity.

The specified volume balances are:

v = L + D + S
e = (1-L)a - D
t = e + v b
q = (1-L)(1-a) - S = 1-v-e.

Here e is bulk primary-pore volume under the chosen convention, q is quartz/framework grain volume, v(1-b) is shale-solid volume and v b is shale-associated pore volume. The conservation identity is q + v(1-b) + t = 1. Connectivity, permeability, reserves and net pay are not implied.

Nonlaminated host fraction is 1-L. Host-normalized primary porosity is e/(1-L); it is withheld when host fraction is numerically zero. This is not a universal clean-sand porosity correction.

Restrict 0<=L<=1, 0<=D<=(1-L)a, 0<=S<=(1-L)(1-a). Reject observations outside the admissible balances. A 1e-9 numerical comparison tolerance absorbs roundoff at vertices; materially invalid inputs are not clipped into solutions.

## Inversion and nonuniqueness

First compute e = t-v b. For the restricted branch where dispersed and structural shale do not coexist:

L_D = (e-a+v)/(1-a)
L_S = 1-e/a
L_max = min(L_D,L_S).

At L_max, D=(1-L_max)a-e and S=v-L_max-D. If both D and S vanish, report a laminated scenario. Otherwise report the corresponding laminated-dispersed or laminated-structural scenario.

The two observations generally do not identify geological texture. Under these assumptions, every L from zero to L_max gives a volume-admissible coexisting alternative with D=(1-L)a-e and S=v-L-D. Record the full L range and representative scenarios at its endpoints and midpoint. Mark samples ambiguous whenever this range has nonzero numerical width. Restricted branch matching never grants interpretation approval.

## Input and applicability contract

- Bind an imported LAS source to a saved M1 geometry revision. Require a matching declared MD datum and preserve raw/Parquet/revision hashes.
- Porosity must be supplied total physical porosity with compatible measurement/derivation and bound-water evidence. Apparent sonic/neutron basis is rejected; no tool response conversion is inferred.
- Exact source units V/V, PU or % are supported for fractional quantities. PU and % convert with factor 0.01. Unit labels must exactly match LAS metadata.
- Shale volume is supplied in fractional units or calculated under an explicitly supplied linear-GR calibration, v=(GR-GRclean)/(GRshale-GRclean). The latter is a calibration scenario, not a universal clay-volume relation.
- Record endmember values/source, correction state, borehole quality, mineral/fluid assumptions and depth alignment/response resolution.
- Raw/unknown correction states withhold interpretation. Supplied-corrected statements remain user evidence, not independently certified facts. Synthetic state and generated examples are restricted to synthetic projects.
- Missing values and depths outside survey coverage are withheld. Preserve source indices and native sample depths without interpolation or imputation. Bound analyses to 1,000 native samples.

## Sensitivity

Test all distinct corners of the entered observation/endmember perturbations: total porosity, shale indicator, sand/shale porosity and, when applicable, both GR endpoints. Record admissible/outside corner counts, restricted branches encountered and ranges of the tested outputs.

These are tested corner ranges, not statistical confidence intervals or guaranteed extrema over a continuous uncertainty domain. Corners outside applicability remain visible; they are not silently included as valid interpretations.

## Verification evidence

Independent tests cover source vertices, pure laminated mixtures, manually accounted dispersed/structural volumes, coexisting textures on the laminated line, zero-host normalization, 200 independently generated forward volume mixtures, fractional/percent/GR equivalence, sensitivity changing branch, excluded corners, missing/raw/outside inputs, invalid endpoint/unit/basis rejection, source ownership/integrity, report immutability and application restart.

Chrome confirmed the generated ten-sample example: eight eligible, five texture-nonunique, one outside model and one missing. Raw correction state withheld all ten. Saved calculations retain every assumption, input, alternative, sensitivity result and source/revision hash.
