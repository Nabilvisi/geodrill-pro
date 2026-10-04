# Research model contracts added in 0.2.0

These are implementation specifications for reproducible research. No engineering authority, manufacturer qualification or field validation is inferred.

## M1 geometry

Use the original minimum-curvature model with exact great-circle tangent interpolation within each survey interval. Integrate the interpolated unit tangent analytically to obtain coordinates at arbitrary MD. Small-angle terms use their linear limits. Translate N/E/elevation into the user's declared frame; the frame label does not perform a CRS transform.

For a horizontal TVD boundary, split a survey arc at vertical extrema, bisect each monotone branch, preserve every crossing, deduplicate tangent points and report coincident horizontal segments as MD intervals. Formation uncertainty is a user-supplied pick band, not a statistical confidence interval. Tool-to-bit offset is metadata and is not used to extrapolate a bit path.

Hole intervals start at MD 0, are contiguous and ordered. Casing must fit inside every covered hole interval, respect survey coverage and avoid radial overlap with nested strings. Wall-loss allowance must leave at least 0.01 mm of numerical wall; this bound is not an operating limit. Planned/installed status and sources are preserved.

Immutable revisions include inputs, results, change note, predecessor, creation time and canonical SHA-256. A stale predecessor returns HTTP 409. Source raw bytes and normalized Parquet are integrity checked.

## M2 restricted casing screens

For effective radii a and b (b is OD/2; a = b minus qualified minimum wall after allowance), uniform internal/external gauge pressures Pi/Po give:

A = (Pi a² - Po b²)/(b²-a²)
B = (Pi-Po) a² b²/(b²-a²)
sigma_r(r) = A - B/r²
sigma_theta(r) = A + B/r²
sigma_z = supplied total axial wall force / [pi(b²-a²)].

Axial tension is positive. The supplied wall force must include applicable pressure-end loads; the kernel does not infer string load transfer. Evaluate both wall surfaces with von Mises = sqrt([(sigma_r-sigma_theta)² + (sigma_theta-sigma_z)² + (sigma_z-sigma_r)²]/2). The thick-cylinder equation reference is [MIT OCW pressure-vessel notes](https://ocw.mit.edu/courses/22-312-engineering-of-nuclear-reactors-fall-2015/eb49bc4f3e701be60ca651c5a109312f_MIT22_312F15_note_L4.pdf).

Screen yield, positive burst differential, positive collapse differential and tension/compression against separately supplied body and connection ratings. Utilization is demand × supplied design factor / (supplied capacity × supplied uniform temperature factor). Yield uses maximum wall von Mises. Missing ratings remain missing even at zero demand. Manufacturer rating sources are required when values are supplied. Every casing must have every mandatory case in the catalogue.

No default factor represents an approved standard. Expanded collapse interaction, bending, torsion, buckling, cement support, detailed temperature profiles, connection combined-load envelopes and operational design approval are excluded. Pipe-length cost excludes connections, installation, cement and logistics.

## M3 exploratory log response clustering

Select up to eight source LAS curves, preserving exact curve units; declare identity/log10 transform, admissible source-value envelope and its basis. Log10 requires a positive declared envelope. Declare the aligned MD datum, tool offsets/response note, correction state and acquisition quality. These are supplied statements, not automatically verified corrections.

At native sample depths, withhold any row with a missing feature, value outside a supplied envelope or depth beyond saved survey coverage. No imputation, interpolation, depth shift or automatic downsampling occurs. Sort samples by MD while preserving their original zero-based normalized source indices. Limit each analysis to 2,500 samples.

Fit population mean and standard deviation only on complete in-range samples in the chosen training interval. Standardize every eligible vector using those preserved parameters. A constant or numerically negligible-variance selected feature withholds the analysis. Require at least 2K eligible training observations and at least K distinct vectors. The 2K bound is an implementation eligibility rule, not a statistical sufficiency claim.

Use ordinary distance-weighted k-means++ initialization and Lloyd updates for three seeds: entered seed, seed+1 and seed+2. Retain the lowest-inertia converged solution. Empty-cluster or assignment-inconsistent starts are not silently repaired or reported as converged. Labels are ordered lexicographically by standardized centers in sorted curve-name order. Fixed inputs and seed reproduce assignments in this implementation; geological meanings are not transferred across analyses.

Distance is Euclidean distance in standardized transformed feature space. It is not a probability. For log10 features, back-transformed response centers are not arithmetic raw means. Report inertia and minimum adjusted Rand index between the selected solution and other converged starts. ARI assesses initialization agreement, not facies correctness or robustness to instrument noise. The methodological reference is the [scikit-learn clustering guide](https://scikit-learn.org/stable/modules/clustering.html).

Sample groups terminate at withheld samples, changes in cluster or native gaps beyond the supplied joining threshold. Their first/last sampled MDs are not interpreted bed boundaries. Raw/unknown correction state remains visible. Cluster-to-facies mapping, supervised labels, validated domain-shift detection and geological confirmation are unimplemented.

Every saved run records source raw/Parquet hashes and its geometry revision/hash; full inputs, scaler, centers and all native assignments are retained in calculation records and fixed reports.
