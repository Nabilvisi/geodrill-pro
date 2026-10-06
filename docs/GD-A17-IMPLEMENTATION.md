# GD-A17 — connected formation geomechanics research

This increment repairs and connects a restricted isotropic elastic solver. It does
not close the original actual-fluid, coupled thermal/poroelastic or multiphase
requirements in [the backlog](research/post-module-17/BACKLOG.md).

## Workflow and preserved evidence

The Formation geomechanics page uses an immutable M1 survey/geometry revision.
POST /api/projects/{project_id}/calculations/geomechanics saves complete typed inputs
and results. Research schemas, revision-bound templates and original SI JSON imports
use the same model name. Original bytes/hash, normalized document hash, geometry hash
and survey hashes survive fixed reports, restart and project-archive restoration.
Changed inputs retain the original document and mark its comparison false.

MD is supplied; TVD and inclination/azimuth derive from the accepted minimum-curvature
path. The declared stress north reference must match the project's true/grid survey
reference. Dataset, geometry and access checks prevent cross-project binding; viewers
can read templates and cannot save studies. Historical results remain immutable.

Synthetic examples explicitly identify generated core and closure records. Historical
project templates contain no invented core certificate or calibration. Certificate
identifiers, hashes and closure quality are supplied assertions. The software does not
verify that a certificate exists or establish an independent engineering review.

## Numerical changes and assumptions

Version GD-A17-geomechanics-stability-2 supersedes the prototype's ignored inclination,
fixed percentage Mogi relief, invented 15% SHmax uplift and clipped fluid density.

Poroelastic uniaxial-strain stress estimates use supplied modulus, Poisson ratio,
Biot coefficient and horizontal strains. The supplied Shmin closure calibration
replaces its modeled estimate; incompatible SHmax/Shmin ordering withholds results.
All stress gradients use the declared survey datum. No default rock properties are
substituted. True/grid reference conversion and calibration-depth extrapolation are
not inferred.

The total stress tensor rotates into survey-oriented axes. Impermeable circular-wall
Kirsch stresses include axial/circumferential shear and all three effective principal
stresses. Mohr-Coulomb uses UCS + q*sigma3 - sigma1. Mogi-Coulomb uses the actual
octahedral shear and mean of maximum/minimum principal stresses. The coefficients
follow [Al-Ajmi and Zimmerman (2009)](https://doi.org/10.1016/j.petrol.2009.05.018).
The current model excludes rock thermal stress, diffusion, plasticity, anisotropic
elasticity and chemical effects.

The first-order fluid constitutive assumption is rho = rho0*(1+c*Pg-alpha*gradient*z).
The hydrostatic equation dPg/dz = rho*g is integrated from Pg(0)=0 at the declared
datum. Compressibility and thermal component changes above 20% withhold the density;
values are never clipped. This is a declared linear research approximation, not an
actual-mud EOS, ECD calculation, multiphase model or energy balance.

Numerical elastic pressure intervals search the explicitly declared equivalent-SG
range, at or above pore pressure. Sign transitions of the worst sampled tensile/shear
margin are bracketed and bisected to 1 Pa. The coarse run uses 360 angles/81 pressure
seeds; the fine run uses 1440 angles/161 seeds. Interval-count differences or boundary
changes above 500 Pa return nonconverged and suppress intervals. Sampling can miss
unsampled regions; this is not a global completeness proof. Range endpoints remain
marked as censored. Interval endpoints are not operational collapse/fracture limits,
approved mud windows or casing-seat recommendations. The old stability_window result
is null; approval_issued and clearance_generated remain false.

## Explicit withholding

Unknown or missing formation evidence; invalid survey MD/TVD or datum/reference;
missing core/closure sources; tangent LOT or acoustic claims without closure;
wellhead pressure without conversion; calibration depth differing by over 1 m;
gradient/at-depth closure disagreement over 2%; UCS/cohesion/friction fit disagreement
over 5%; inconsistent stress ordering; excessive linear-density corrections; and
failed numerical refinement are disclosed. These are declared research consistency
criteria, not independent measurement acceptance limits.

## Verification and remaining scope

Tests independently check Mogi/MC triaxial equivalence and intermediate-stress response,
vertical principal-stress pressure roots, tensor rotation/eigenvalue invariants,
hydrostatic integration against RK4, zero-coefficient limits and all withholding
conditions. Connected checks cover original imports, save/citations/report/restart,
archive restoration, changed evidence, survey/reference failures and team access.
Browser checks exercise nested core/calibration forms and saved result reopening.

Original core/LOT/PVT observations, actual characterized-fluid adapters, coupled
thermal/poroelastic or multiphase experiments, property-range validation, independent
blind comparisons and named specialist review remain unfinished. They are retained
in the delivery matrix; no field qualification or equipment authority is implied.
