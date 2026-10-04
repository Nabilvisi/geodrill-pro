# Modules 12–17 numerical and evidence specification

Version 0.8.0. Previous equations and eligibility rules remain in MODEL-SPECS-0.5.md through MODEL-SPECS-0.7.md. All new inputs are strict finite SI contracts; unknown evidence abstains. Input provenance is declared, not independently authenticated. Every saved study binds the selected immutable geometry and original/normalized survey hashes.

## M12 reduced dynamics

A uniform straight cantilever segment uses three generalized coordinates q = [axial displacement m, torsional angle rad, lateral displacement m]. Area A = π(OD²−ID²)/4, I = π(OD⁴−ID⁴)/64, J = 2I, shear modulus G = E/[2(1+ν)].

Diagonal generalized masses are ρAL/3, ρJL/3, and 0.236ρAL. Stiffness diagonals are EA/L + supplied bit stiffness, GJ/L, and 3EI/L³. Supplied dimensionless couplings multiply the geometric mean of the corresponding diagonal stiffnesses; the correlation matrix must be positive definite. These are declared reduced-coordinate assumptions, not a fitted BHA model.

M q̈ + C q̇ + K q = sinusoidal excitation + bilateral lateral clearance-spring contact. Diagonal damping Cᵢ = 2ζ√(MᵢKᵢ). A Jacobi symmetric eigensolver evaluates M⁻¹ᐟ² K M⁻¹ᐟ². Reported vectors use mass-normalized generalized coordinates; they are not spatial/observed mode shapes. Frequencies are √λ/(2π).

Explicit RK4 integrates from zero displacement/velocity. At least 40 steps per highest excitation or contact-active linearized cycle are required. Coarse/fine responses are compared at the complete coarse time history; energy includes contact potential. External work and dissipated energy use trapezoidal quadrature. Response differences above the supplied refinement tolerance return incomplete_assessment.

The structural interval must fit accepted survey and complete hole geometry; curved segments and unsupported boundaries abstain. OD/clearance must fit intersected holes and installed casings. Planned casing is not treated as installed confinement.

Native channels preserve sample times, value/null, quality, axis, units and declared anti-alias bandwidth. Accepted values and sufficient sampling allow descriptive RMS and bandwidth eligibility only. Calibration is not independently verified; no state estimator or modal-observability claim is issued.

Verification: independent uncoupled modal frequencies; zero-initial-condition sinusoidal axial closed form; fourth-order error reduction; coupled/contact energy and refinement; clearance and sampling gates.

## M13 inspected runs and censored cohorts

Each run retains bit serial/family, formation, well, hours, footage, recovery/termination, inspected grade/note, photo reference, evidence availability, and optional energy with its measured-bit/surface-proxy basis. Completed_at means the end of the recorded observation; an ongoing run is a censored observation, not a completed physical run.

Eligibility requires matching family/formation, known termination and available_at at or before the cutoff. Availability must not precede recorded observation completion. Post-recovery inspection information cannot enter an earlier cutoff.

Kaplan–Meier S(t) = product over failure times of [1−dᵢ/nᵢ]. At tied times, failures use the risk set before removing censoring. Greenwood variance and clamped normal limits are descriptive. Independent censoring is assumed; planned-trip censoring can be informative and endpoint intervals are withheld because the normal approximation degenerates there. No fitted calibration or held-out performance is claimed.

Within observed support, horizon failure fraction = 1−S(age+horizon)/S(age). Continue cost = fraction × supplied unplanned-failure cost + horizon × supplied hourly cost. The comparison has no recommended action. Insufficient records, no failures, no survivors or unsupported horizons withhold the applicable output.

Verification: tied risk sets/product limits, censoring, receipt-time leakage, inspection contract, support and conditional cost arithmetic.

Reference: NIST Kaplan–Meier documentation, https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/kaplan.htm .

## M14 wear, fatigue and uniform-wall pressure screen

Contact exposure is Σ F_N L in N·m. Wear V = k × exposure with k in m²/N, followed by depth V/patch area. A supplied relative coefficient corner produces a conservative scenario wall. It is not a confidence interval. Missing coefficient retains exposure while withholding predicted wear.

S–N cycles interpolate linearly in log stress/log cycles within supplied support only. Zero stress contributes zero damage. Miner D = Σ n/N is separate from wear. Nonzero mean stress, absent data or unsupported amplitude withhold the fatigue result; previously entered spectra remain preserved in inputs. No sequence/corrosion/crack-growth model or inferred missing cycles exists.

A restricted closed-end Lamé/von Mises pressure screen requires uniform positive conservative wall, declared complete exposure and supplied yield/source. Localized grooves and unobserved exposure abstain. Planned casing and all results remain scenarios. Connection capacity and barrier acceptance are not assessed.

Inspection residual = observed minimum wall − predicted scenario wall; supplied inspection uncertainty remains distinct. Positive or negative residual is not calibration or certification.

Verification: coefficient dimensions, independent pressure/yield expression, wear corner, log–log fatigue interpolation, separate mechanism gates and inspection residual.

## M15 causal mass balance

On each native adjacent interval, r = trapezoidal(inlet − outlet + signed transfer) − Δcontained_mass/Δt, in kg/s. A positive transfer enters the declared control volume. No undocumented resampling, gap filling or pressure-to-inventory inference occurs.

Accepted/nonnegative numeric inlet/outlet/stock, known transfer and a gap within the supplied limit are required for balance. Circulating/pump-on state at both interval ends is additionally required for candidate monitoring. Null/suspect/negative/gap intervals retain unknown_balance and interrupt persistence; operation changes retain balance where available but do not produce a monitored candidate.

A candidate requires |r|−supplied allowance ≥ threshold with the same sign for the supplied duration. Alarm availability is the interval end, never its onset. Native observations remain separate from interval calculations.

Supplied adjudicated labels match one candidate each by alarm time inside the label interval. All missed labels and unmatched candidates are retained. False candidates/hour uses eligible monitoring duration. Lead = baseline alarm − candidate alarm; no probability calibration, operational diagnosis or field performance is claimed.

Verification: transfer/stock sign, exact zero balance, prefix causality, state/null/gap resets, all misses/unmatched candidates, onset/availability and baseline lead.

## M16 characterized equilibrium and external replay

Native research supports exactly two characterized nonpolar components with normalized positive composition. Classical Peng–Robinson mixing uses aᵢ = 0.45724 R²T_c²α/P_c, bᵢ = 0.07780 RT_c/P_c and supplied k₁₂; κ = 0.37464+1.54226ω−0.26992ω². PR roots must satisfy Z>B.

A feed root minimizes its molar residual Gibbs value. Four binary trial seeds evaluate tangent-plane-distance iteration; failure to converge abstains. This finite trial search is not a global multicomponent stability proof. An unstable feed requires bracketed Rachford–Rice split, normalized phase compositions, nontrivial split, material closure and component fugacity equality. Single stable states do not manufacture a vapor fraction.

The supplied synthetic methane/ethane example uses rounded properties; it is a numerical verification case, not drilling-fluid characterization. Unsupported actual-mud use of the native binary EOS abstains.

External review requires a named exact model/reference and review note, normalized phase compositions, declared convergence/stability flags and material residual within the supplied tolerance. Those flags remain supplied and are not independently verified. MD must fit the accepted survey. Original documents are preserved.

Batch replay uses a fixed total gas inventory, supplied equilibrium dissolved-gas targets and prescribed gas molar volumes. Targets and volumes interpolate between external points. Dissolved inventory relaxes exponentially over each substep with endpoint-held target; free = total−dissolved. Full-history N/2N/4N refinement measures discretization error. This is neither a wellbore transient simulator nor a momentum/energy/slip/transport solution.

Verification: known cubic/Rachford roots; original EOS pressure substitution; two-phase composition/fugacity/material closure; dilute high-temperature single state; exact constant-target relaxation; conservation, external flags/depth and refinement.

Reference for PR coefficients, mixing and fugacity: IDAES cubic EOS documentation, https://idaes-pse.readthedocs.io/en/2.11.0rc1/explanations/components/property_package/general/eos/cubic.html .

## M17 isolated supervisory software simulation

The plant dp/dt = (p_zero + gain × u − p)/τ integrates exactly for a held actuator over each step. Bounded discrete PID uses explicit gain units, conditional integral anti-windup and rate-bounded desired trajectory. Delayed requests follow that trajectory rather than using stale accepted feedback as the demand ramp. Coarse/fine complete-history pressure comparison is required.

An independent software validator checks logical simulation lease, exact canonical configuration hash, target/unit allowlist, issue/expiry/TTL, duplicate ID, accepted-request rate, value and slew envelope, supplied simulated process pressure, connected/readiness/manual/known state. Rejections do not consume accepted-request state. Manual override uses an explicit supplied simulation position. Faults discard pending requests and require fresh post-recovery delivery.

The hash covers all input configuration, evidence context and faults except the display name and self-referential example requests. The example-request audit uses the declared initial scenario pressure, not a real independently observed plant state.

The supplied process envelope constrains simulated request validation and reports any exceeded pressure scenario. It does not create independent protection or a process-specific fallback. Holding a simulated actuator after rejection is an explicit plant assumption. No production authority, authenticated operator lease, rig network, PLC register, OEM adapter or equipment-command route exists.

Verification: exact zero-controller first-order response, tracking refinement, envelope bounds, changed configuration, duplicates/expiry/rate/slew, lease expiry, delayed TTL, fault rejection/manual override and fresh reconnect timing.

## Delivery and interpretation

Numerical verification checks equations and software contracts. None of these tests establishes laboratory calibration, sensor qualification, physical prediction accuracy, early-kick performance, casing integrity, rig protection or permission to operate. Software statuses are research_scenario, withheld, incomplete_assessment and outside_scenario_envelope as applicable. Equipment authority remains none.
