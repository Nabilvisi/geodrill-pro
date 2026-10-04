# Module 11 numerical specification — version 0.7.0

This release implements the audited **offline buckling screening** scope in part-1 §5.11 and GD-037. It does not implement production-qualified general 3D post-buckling. API model: buckling; kernel: packages/engineering/buckling.py; UI: Buckling assessment.

## Inputs and source binding

Each immutable study includes a saved M1 revision, project MD datum, selected M10 calculation, evidence state, explicit interval, modulus and provenance, contact configuration, end-boundary declaration, force basis, uncertainty and optional conditional load-transfer settings. The selected M10 record supplies OD, ID, steel density, fluid density, friction and operating direction. Source ownership, exact geometry/datum and preserved calculation integrity are checked before evaluation; SHA-256 of the full source is saved. Original survey and geometry hashes are retained.

The M10 buoyed soft-string force is treated as an **effective-force baseline** under that model's equal internal/external density assumption. It is not measured wall force. The baseline cannot be pressure-corrected a second time. Alternatively, the user supplies strictly ordered endpoint-covering knots of wall tension and internal/external **absolute** pressures on the same reference:

T_eff = T_wall - P_i A_i + P_o A_o

Tension is positive; compression C = max(0, -T_eff). Piecewise-linear wall/pressure inputs and M10 source forces are evaluated with every load knot retained. A local compression allowance shifts the uncertainty force envelope; no surface WOB is substituted for local force. Supplied evidence cannot be established by a synthetic M10 source.

## Selected confined-pipe formulation

A = π(OD² - ID²)/4; I = π(OD⁴ - ID⁴)/64; EI = E I.

Buoyed weight per length w = (steel density - common fluid density) g A.

Actual installed bore diameter is the minimum of the hole diameter and installed casing IDs. Planned casing is not treated as installed. Radial clearance r = (bore ID - OD)/2.

For straight, inclined, uniform plain pipe, with inclination θ measured from downwards vertical:

- Dawson–Paslay sinusoidal estimate F_s = 2 sqrt(EI w sin θ / r).
- Selected Chen–Cheatham helical estimate F_h = sqrt(8) sqrt(EI w sin θ / r).
- Characteristic wavelength λ = 2π (EI r / (w sin θ))^(1/4).

This is a named formulation, not a universal helical-onset coefficient. Thresholds are compared separately with local effective compression. Mode indicators are tension, below sinusoidal, sinusoidal susceptibility and helical susceptibility. A susceptibility indicator is not a solved or observed buckling shape. Point counts do not represent interval lengths.

The selected formulas are documented in the [BSEE-hosted Maurer BUCKLE1 manual](https://www.bsee.gov/sites/bsee.gov/files/tap-technical-assessment-program/300an.pdf), theory §§2.2.1 and 2.2.3, and the [Liang and Zhu paper, DOI 10.1016/j.petrol.2018.05.053](https://www.sciencedirect.com/science/article/abs/pii/S0920410518304479). The effective-force definition is independently supported by [Controlling lateral buckling of subsea pipeline with sinusoidal shape pre-deformation](https://www.sciencedirect.com/science/article/pii/S0029801818300246). The stored reference list is preserved with results.

## Eligibility and withholding

Every intersected minimum-curvature survey arc is checked; matching interval-end tangents do not conceal internal curvature. Eligible inclination is 5–90 degrees. The 5-degree cutoff is a conservative software scope choice; it is not a physical vertical-buckling threshold.

The selected interval must have one string section, uniform installed bore, positive clearance, positive buoyed weight, no applied torque or operating rotation, uniform plain pipe, and the explicitly declared long-pipe boundary with unrestrained end rotation. Pinned, clamped, unknown, jointed/stabilized, curved, vertical/upgoing, and diameter-transition cases are saved as withheld. Geometry/load coverage failures reject the input.

The interval must span at least ten characteristic wavelengths, including the largest uncertainty-corner wavelength. **Ten wavelengths is an eligibility guard, not a validated proof that end effects vanish.** End restraint evidence remains necessary; there is no finite-length nonlinear contact model in this release.

Compression at nominal/uncertainty knots must stay below a 0.2% elastic axial-strain screen. This software envelope is not a supplied yield rating or a material certificate. Actual material yield, thermal effects, residual curvature and combined stress qualification remain open.

## Sensitivity

Modulus and radial-clearance uncertainty are relative, bounded at 0–50%. Threshold ranges use the exact monotone corner combinations: low EI/high clearance and high EI/low clearance. Local compression uncertainty is an independent absolute force allowance. Nominal margins and conservative margins remain separate.

Friction uncertainty must stay within [0,1]. It is used in the optional transfer scenario. Neither friction nor observed M10 residuals establish calibration.

## Conditional helical load transfer

For a requested ideal-helical axial-drag scenario, the interval bottom **effective tension is prescribed** from the selected force basis. A separate upward force equilibrium is integrated; the M10 profile is retained as the original screen baseline.

At C ≥ F_h, conditional added normal force per length is n_b = r C²/(4EI). Below that branch, n_b = 0. Normal weight contact is w sin θ. The upward force equation is:

dT/dx = w cos θ + sign(v_up) μ [w sin θ + n_b]

The [2025 helical post-buckling paper](https://link.springer.com/article/10.1007/s13202-025-02009-4), its weightless limiting contact relation following Eq. 22, supports the ideal contact expression. Adding normal-weight contact and Coulomb axial slip is the explicitly selected reduced modelling assumption. It does not solve periodic gravity contact, residual bending, hysteresis or the sinusoidal-to-helix transition. Sinusoidal post-buckling added contact is omitted. This conditional scenario is not a general nonlinear beam/contact solution or a lock-up prediction.

Fourth-order Runge–Kutta uses N, 2N and 4N cells. Shared-node differences cover the entire nominal profile and all 16 modulus/clearance/friction/bottom-force corners. Completion requires the worst refined-profile difference to satisfy the supplied force tolerance. Branch divergence, non-finite/over-limit force, ideal-helix slope r sqrt(C/(2EI)) > 0.2, or uncertainty-branch strain beyond the elastic envelope produce an incomplete assessment, retaining the original screen and an explicit transfer reason.

The resulting upper effective tension, unbuckled comparison, upper-force change and tested corner range are shown separately. These apply only to the selected interval and prescribed bottom force, not the entire surface hookload or an operational bit-load limit.

## Verification and remaining qualification

Numerical verification includes published-formulation dimensionless coefficients with manufactured SI inputs, an independently evaluated sinusoidal Rayleigh energy minimum, and an independent horizontal constant-helix Riccati solution. These checks reproduce selected equations; they are not experimental validation. Tests also cover pressure signs, distinct onset states, uncertainty, installed/planned clearance, hidden curvature, unsupported boundaries, convergence, divergence, source ownership/datum, report inclusion and reopening after restart.

Independent structural analysis, measured laboratory confined-pipe tests and defensible field cases remain required before production use. Dynamics/BHA interactions belong to the later M12 scope. No equipment authority or approval is issued.
