# Module 6 — steady geometry-linked hydraulics / version 0.5.0

This implements a declared research envelope within audit Part 1 section 5.6: steady, closed, incompressible single-phase circulation, fully developed laminar flow, stationary concentric walls and constant fluid density/rheology. It does not qualify an operational pressure window or implement turbulent/transitional, eccentric, rotating, cuttings-loaded, thermal/compressible, gas, loss or transient flow closures.

## Records, geometry and gates

Inputs preserve the scenario timestamp and maximum acceptable mud-test age; a separate measured-at timestamp, fluid evidence state and source; density, test temperature, rheology law and pressure/temperature applicability note; string sections; nozzle area/coefficient and their source; supplied upstream surface loss and its flow basis; pressure-window knots, allowances, reference and review state; a supplied surface-supply rating/source; and tested sensitivity perturbations.

Mud age is scenario_at minus measured_at, using explicit UTC offsets. A future mud record or age above the supplied maximum withholds the calculation. Unknown mud evidence or unreviewed pressure limits withhold it. This is historical scenario evaluation, not live-data freshness or laboratory verification. Synthetic evidence and generated examples are restricted to synthetic projects.

The chosen immutable M1 revision supplies directional-survey geometry, contiguous hole sections and casing IDs. The API verifies project ownership and raw/Parquet survey integrity, then binds geometry and survey hashes into the saved calculation. Hydrostatic depth is TVD relative to the declared datum; friction length is MD along the actual survey path. No magnetic/CRS transform or tool-to-bit extrapolation is performed.

String sections must cover the path contiguously from MD 0 to the chosen circulation depth. Section breaks, hole/casing transitions, survey stations and pressure-limit knots define hydraulic intervals. Installed_only uses installed casing IDs; include_planned_scenario explicitly adds planned casing IDs. The innermost included casing ID, or the hole diameter where uncased, defines the outer flow boundary. Planning inclusion is not installation evidence.

The entire circulation path needs hole/survey coverage. String OD must leave at least 1 mm diametral clearance. The numerical radial envelope requires radius gap at least 0.5 mm, inner/outer annular radius ratio 0.02–0.98 and at most 1,000 hydraulic intervals. Positive flow below 1e-10 m3/s is withheld rather than rounded to static flow; exactly zero flow is a separate hydrostatic case.

## Rheology and radial flow

The yielded constitutive relation is |tau| = tau_y + K*|gamma_dot|^n. Unyielded regions have zero shear rate; they are not treated as zero viscosity.

- Newtonian: n=1, tau_y=0, K is viscosity in Pa.s.
- Bingham: n=1, K is plastic viscosity in Pa.s.
- Herschel–Bulkley: K has units Pa.s^n, n is dimensionless; supported numerical n range is 0.2–1.5.

For a pipe radius R and positive friction pressure gradient F in Pa/m, |tau(r)|=F*r/2. The flow integral is Q=pi*integral(gamma_dot*r^2 dr), beginning at the yielded radius. The implementation evaluates that integral analytically for HB, retaining its plug; Newtonian and Buckingham–Reiner limits are independently tested.

For concentric annular radii a,b, the signed shear is:

tau(r) = F/2 * (r0^2/r - r).

The constitutive law gives du/dr=sign(tau)*((max(0,|tau|-tau_y))/K)^(1/n). The unknown zero-shear radius r0 satisfies integral_a^b(du/dr dr)=0, imposing no slip at both walls. Yielded domains are integrated separately, with the intervening unyielded region preserved. Annular rate is Q=pi*integral_a^b((b^2-r^2)*du/dr dr). This is the radial annulus solution; a hydraulic-diameter pipe or planar-slot substitution is not used for laminar annular loss.

Both geometries solve Q(F) monotonically for the supplied rate. Annular quadrature begins at 48 Gauss–Legendre points and checks 96 points. If needed, it solves at 96 and checks 192. Relative flow change must remain within 3e-5; failed bracketing/convergence or friction gradient above 1e7 Pa/m withholds the case. The supplied numerical envelope is implementation eligibility, not an operating limit.

## Applicability screens

A flowing case requires supplied_laminar evidence, with an explicit applicability note. Additional nominal-apparent Reynolds screens use:

- Pipe nominal shear = 8*mean_velocity/ID.
- Annulus nominal shear = 12*mean_velocity/(bore_ID-string_OD).
- Apparent viscosity = tau_y/nominal_shear + K*nominal_shear^(n-1).
- Re_screen = density*mean_velocity*hydraulic_diameter/apparent_viscosity.

A screen above 1,000 withholds the case. This deliberately restricted screen is **not a validated non-Newtonian transition correlation** and does not prove laminar flow. Nonzero eccentricity, rotation or cuttings fraction withholds the current closure. Relative roughness must be no more than 0.001 of the relevant pipe/hydraulic diameter for the smooth-wall approximation.

Density, K, n and yield stress stay constant along the path. Test temperature is preserved as evidence; no temperature/pressure correction is silently inferred. Local transitions, bends, tool joints, entrance flow, viscoelasticity, thixotropy and cavitation are not resolved. Actual applicability and measured validation remain open.

## Pressure references and circulation balance

All pressures use gauge relative to atmospheric pressure at the surface datum. For MD s, TVD z(s), constant density rho and return backpressure Pback:

Annular_pressure(s) = Pback + rho*g*z(s) + annular_loss_from_surface_to_s.

Standpipe_gauge = Pback + total_annular_loss + total_pipe_loss + nozzle_loss.

Pipe_pressure(s) = Standpipe_gauge + rho*g*z(s) - pipe_loss_from_surface_to_s.

Required_supply_gauge = Standpipe_gauge + supplied_upstream_surface_loss.

Nozzle_loss = rho/2 * (Q/(Cd*total_nozzle_area))^2.

Thus the bottom pipe-minus-annular pressure equals nozzle loss. Surface equipment loss is upstream of the standpipe reference, not falsely carried through the pipe profile as an additional bit loss. The supplied surface-supply rating is compared with the maximum tested **required supply** pressure.

At Q=0 all calculated pipe/annular/nozzle losses and upstream friction loss are zero. The source input remains preserved. For nonzero sensitivity flow corners the supplied upstream loss is held fixed; it has no fitted flow law.

Displayed equivalent density = annular_gauge_pressure/(g*TVD), explicitly including backpressure. It is null at TVD <= 0, including horizontal-at-datum paths. Above-datum trajectories are withheld because absolute-pressure/phase evaluation is not implemented.

Specified inlet/outlet mass flow is rho*Q by the imposed closed-circulation boundary. Returned radial-flow residuals and the independently tested bottom pressure balance provide separate numerical checks. The sum of segment loss times quadrature rate change is a **numerical change indicator**, not a rigorous pressure-error bound or an allocated field error budget.

## Pressure limits, continuous margins and sensitivity

Limits are supplied pore/fracture gauge-pressure knots, piecewise linear in **MD**, with a source and review note. They must cover the complete circulation path. Each pore upper allowance raises the assessed lower bound; each fracture lower allowance lowers the assessed upper bound. Allowances may overlap; negative margins are retained rather than clipped. The evidence state is a supplied declaration, not an independently authenticated approval.

Lower margin = annular pressure - (supplied pore pressure + upper allowance).

Upper margin = (supplied fracture pressure - lower allowance) - annular pressure.

Within each constant-friction/linear-limit/minimum-curvature interval, margin derivative depends on rho*g*dTVD/dMD plus friction gradient minus limit slope. The solver finds tangent-direction roots analytically along each arc and checks interval endpoints and TVD extrema. The small-angle interpolation branch is handled consistently. Minimum margins therefore include interior arc extrema rather than relying only on survey endpoints or the plotted grid.

Sensitivity tests the Cartesian endpoint corners of four supplied perturbations: density, flow, K and backpressure (up to 16 distinct cases). Pressure allowances are also used. Other physical parameters remain fixed. Requested corners outside model applicability are saved with reasons and make the assessment incomplete. Ranges are tested scenarios, not confidence intervals or proven bounds over every continuous parameter combination.

Nominal/corner limiting MD, TVD, pressure and parameters are saved. Profile plots show nominal/static pressure, assessed limits and corner ranges on the evaluated sample grid. Profile points include hydraulic boundaries, nominal extrema, regular samples and sensitivity limiting locations. The table initially shows 100 points; the complete profile, all interval diagnostics and corner summaries remain in the report.

scenario_only means a complete research comparison was calculated; negative margins do not change it into approval. incomplete_assessment identifies missing rating or withheld sensitivity corners. Withheld calculations contain no nominal profile. A positive within_all_tested_bounds flag remains conditional on the chosen model and supplied evidence; approval_issued is always false.

## Verification and source context

Fifty-two additional tests cover independent Newtonian pipe/annulus formulas, Buckingham–Reiner pipe limits, independent elementary Bingham-annulus antiderivatives, power-law pipe limits, dense-grid HB velocity integration and quadrature refinement, zero/unyielded limits, SI/reference semantics, mass/bottom-pressure balance, segmented geometry, planned/installed separation, sensitivity and equipment margins, stale/future/unknown records, outside-model states, datum/coverage gates, tiny-flow resolution, ownership, immutability/report/restart and source corruption.

A curved-well reference proves the importance of interior checking: both endpoint upper margins are positive, while the exact interior upper margin is negative; the implementation locates that crossing/extremum independently of plotting spacing.

The Newtonian annulus benchmark uses a=57.15 mm, b=107.15 mm, viscosity 0.001 Pa.s and Q=0.0005 m3/s. Its independent analytical gradient is 0.092393855 Pa/m, agreeing with the published rounded 0.09239. This is a kernel verification case, not profile eligibility or field qualification; its Newtonian Reynolds number exceeds this application's deliberately restricted 1,000 screen.

Primary source: Nikitin, Journal of Mining Institute (2022), https://pmi.spmi.ru/pmi/article/view/15839 . The web-rendered velocity expression is dimensionally incomplete, so the implementation derives flow from the signed stress law/no-slip conditions and verifies it independently rather than copying that display. No cuttings-removal, optimum-fluid or operational claims from the paper are adopted.

No API RP 13D edition/method is adopted as a compliance basis in this release. This solver uses the stated momentum/constitutive construction. Turbulent/transition and environmental corrections, expanded component/casing ratings, thermal/compressible and transient coupling, instrumented flow-loop/PWD comparisons, calibrated uncertainty and allocated acceptance/error budgets remain separate required qualification work.
