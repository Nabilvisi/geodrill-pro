# Model specifications — version 0.6.0 / Modules 7–10

This release completes working research subsets through M10. Each study binds an immutable M1 revision, original survey hash and normalized-source hash. M8/M9 additionally bind the complete preserved M6 study by SHA-256. Historical projects cannot accept synthetic input evidence or generated hydraulic sources. Source integrity, project ownership and datum checks execute before calculation.

All inputs use canonical SI units. The editor displays pressure in MPa, Young modulus in GPa, force in kN, torque in kN.m, flow in L/min and ROP in m/h. Input limits are numerical eligibility limits, not operating limits. Unknown evidence and unsupported model states are saved as withheld results. A saved result is never recalculated implicitly after editing its draft.

## M7: elastic and restrained-wall thermal scenario

The reference frame is north/east/down; compression is positive. The supplied symmetric total stress tensor must be positive semidefinite. Biot coefficient is fixed at 1. Effective far-field stress is total stress minus pore pressure times the identity. The accepted minimum-curvature tangent and an orthonormal transverse basis rotate the full tensor into local borehole axes; stored basis vectors make circumferential-angle interpretation reproducible.

For a circular wall with perfect impermeable mudcake, support is Pw-Pp. For local effective stresses x,y,z,xy,xz,yz and circumferential angle theta:

    dev = (x-y) cos(2 theta) + 2 xy sin(2 theta)
    hoop = x+y - 2 dev - support + thermal
    axial = z - 2 nu dev + thermal
    shear_theta_z = 2 (yz cos(theta) - xz sin(theta))
    radial = support

Tangential/axial principal stresses are the eigenvalues of the symmetric 2x2 block; combine with radial stress and order them. Tensile margin is minimum principal stress plus supplied tensile strength. Mohr-Coulomb margin is UCS + q * minimum principal - maximum principal, q=(1+sin(phi))/(1-sin(phi)). Negative margins are retained and explicitly flagged; they do not establish operational collapse, fracture propagation or losses thresholds.

The optional thermal term is E*alpha*DeltaT/(1-nu), with DeltaT = wall minus initial temperature. Cooling is negative in this compression-positive convention. This is a uniform restrained-wall estimate applied to hoop and axial components; no heat equation, transient radial temperature solution or coupled pore diffusion is implemented. Selecting anisotropy, plasticity or coupled poroelasticity withholds the calculation.

Angular checks evaluate 360 and 1,440 points. Results report the change in sampled minima, limiting angles and 0.25-degree refined resolution. This is a sampled refinement indicator, not an interval error certificate.

Optional external lower/upper pressures require ordered values, evidence state and provenance. An externally_approved label preserves the supplied assertion; approval_verified remains false. M7 generates no operating pressure limits.

The vertical benchmark uses SH=22 MPa, Sh=13 MPa, Pw=Pp=10 MPa, giving hoop extrema -3 and 33 MPa before thermal effects. Additional tests cover thermal signs, isotropic rotation invariance, principal-stress trace/determinant, invalid tensors, strength exceedance and unsupported models. Reference: [Espinoza, Introduction to Energy Geomechanics, wellbore stability](https://dnicolasespinoza.github.io/ch6_WellboreGeomech.html).

Open qualification: coupled thermal/poroelastic manufactured solutions and convergence, permeability/thermal histories, anisotropy/fractures/plasticity, independently reviewed geomechanical inputs, strength calibration and instrumented field validation.

## M8: dilute vertical Stokes-slip solids inventory

M6 supplies the declared concentric bore/string geometry, fluid density, Newtonian viscosity and unchanged circulation flow. Particle shape must be spherical, particle density above fluid density, settling Reynolds number <=0.1, inclination <=10 degrees and rotation zero. Non-Newtonian rheology, irregular particles and deviated-bed transport are unsupported.

    A = pi*(bore_diameter^2 - string_OD^2)/4
    fluid_velocity = flow/A
    settling_velocity = (rho_particle-rho_fluid)*g*particle_diameter^2/(18*viscosity)
    upward_particle_velocity = max(0, fluid_velocity-settling_velocity*cos(inclination))
    generation = bottom_hole_area * ROP

Axial intervals form bottom-to-top well-mixed tanks. Tank volume is A*MD length; removal rate is upward particle velocity/MD length. Each implicit backward-Euler step transfers precisely the volume leaving a tank into the next tank. The generation stop is inserted as an exact time boundary, including non-grid-aligned stop times.

    inventory_new = (inventory_old + incoming_volume)/(1 + dt*removal_rate)
    outgoing_volume = dt*removal_rate*inventory_new
    initial_inventory + generated - returned - current_inventory = residual

The output retains volume balance, generated/returned/retained history, concentration by depth and peak concentration/time/interval. Nominal and half-time-step runs report returned-volume change. A computed solids fraction above 5% changes status to outside_dilute_envelope; retaining that numerical result is not a qualified dense-flow solution. Work is bounded by 20,000 steps and two million tank-step operations per run.

This is a tank residence-time model. No sharp advective front, axial spatial convergence certificate, horizontal bed/deposition law or universal critical cleaning velocity is claimed. At zero upward transport, retained inventory grows without a deposited-bed closure. No change to linked M6 flow or pump recommendation occurs; its tested pressure/rating state remains explicit.

Tests independently recover Stokes velocity and annular area, the single-tank backward-Euler solution, exact source stopping, zero-source/zero-outflow limits, conservation and applicability failures. Low-Reynolds/Stokes context: [Miedema, Slurry Transport, dimensionless numbers](https://eng.libretexts.org/Bookshelves/Civil_Engineering/Slurry_Transport_(Miedema)/02:_Dimensionless_Numbers_and_Other_Parameters/2.02:_Dimensionless_Numbers).

Open qualification: non-Newtonian settling and hindered settling, particle shape/size distributions, turbulent/eccentric/rotating flow, horizontal bed inventory, solids-return measurements and independent loop/well comparisons.

## M9: offline reduced acoustic piston surge/swab

M6 supplies constant density/viscosity, uniform annulus dimensions, backpressure and pressure-window knots. The modeled MD interval must be fully covered by the same saved geometry; diameter transitions and non-Newtonian transient drag are withheld. The initial state is static. M6 circulation pressure is not silently used as the initial transient state.

The coordinate points upward from interval bottom to top. Downward pipe speed is positive. Piecewise-linear motion knots specify ramp, travel and pause; initial speed must be zero. Closed-end displacement area is pipe OD area; open-end instantaneous-fill displacement is metal area. This is a declared reduced displacement boundary, not a full pipe-motion hydrodynamic model.

    partial_t(pressure_perturbation) = -rho*c^2*partial_x(fluid_velocity)
    partial_t(fluid_velocity) = -partial_x(pressure_perturbation)/rho - lambda*fluid_velocity
    bottom_velocity = displacement_area/annular_area * downward_pipe_speed
    top_pressure_perturbation = 0

Effective acoustic wave speed c is supplied with provenance; its fluid/structure compliance is not inferred. Lambda is the exact Newtonian concentric-annulus steady gradient divided by rho*velocity. Pipe-wall entrainment, internal flow transients, gel, gas, variable area and nonlinear inertia are excluded.

The staggered finite-volume solver uses cell-center pressure and face velocities, leapfrog momentum, centered implicit linear drag and continuity with the same boundary fluxes used in the conservation record. CFL <=0.45. Domain movement must stay <=1% of interval length, including exact displacement extrema at velocity zero crossings.

Equivalent compressible storage volume is A*dx*sum(p)/(rho*c^2). Its change equals integrated bottom inflow minus top outflow to roundoff. The reported relative storage perturbation is p/(rho*c^2); it is not a separately inferred fluid-density change when c includes wall compliance.

Every scenario runs N,2N,4N cells with correspondingly refined time steps. Extrema are compared after aggregating finer extrema onto each coarser interval. The latest change must meet the explicitly supplied pressure tolerance. It is a refinement indicator, not a certified bound. Runs exceeding 25,000 steps or three million cell-step operations are rejected.

Every fine cell/time contributes to its minimum/maximum pressure and supplied lower/upper margin. The fixed top boundary is checked separately. Peak Reynolds >1000, storage perturbation >1%, vacuum crossing under the declared 101325 Pa atmospheric assumption, pressure-window crossing and unmet refinement tolerance remain explicit incomplete-assessment conditions. No whole-well continuous-bound claim or trip-speed advice is issued.

Tests cover exact static zero, Joukowsky p=rho*c*u before reflection, sign reversal, compressible-storage conservation, persistent reflected pressure during a pipe pause, three-grid diagnostics, strict tolerance failure, moving-domain and diameter-transition gates. References: [COMSOL water-hammer equations](https://doc.comsol.com/6.3/doc/com.comsol.help.pipe/pipe_ug_fluidflow.05.43.html) and [its Joukowsky verification case](https://doc.comsol.com/6.3/doc/com.comsol.help.models.pipe.water_hammer_verification/water_hammer_verification.html). The implementation is a local reduced solver; no COMSOL simulation or equivalence is claimed.

Open qualification: moving mesh/full displacement and entrainment, internal fill boundaries, variable geometry/compressibility, gel/non-Newtonian closures, gas/cavitation, independent transient simulator comparisons, time/space error budgets and pressure observations.

## M10: quasi-static soft-string torque/drag and existing MSE

MSE remains the separately qualified research subset in Engineering lab. Torque/drag binds M1 trajectory, complete contiguous string sections, material/fluid density, effective contact radius, supplied friction, bottom tension/torque and explicit pickup/slackoff/rotating/combined motion.

Tension is positive; axial speed is positive upward. Pickup/slackoff require signed axial speed and zero rotation. Rotating requires nonzero rotation and zero axial speed. Combined motion requires both. Static Coulomb friction without direction is not guessed.

For each interval, buoyant metal weight per MD is (rho_material-rho_fluid)*g*pi*(OD^2-ID^2)/4. With downward unit tangent t and curvature k, transverse contact per MD is the norm of T_mid*k - weight*(down - t_z*t). This follows from vector soft-string equilibrium; no bending stiffness is present.

    contact = norm(T_mid*curvature - weight*projected_gravity)*MD_length
    resultant_slip_speed = hypot(axial_speed, contact_radius*rotation)
    axial_fraction = axial_speed/resultant_slip_speed
    rotational_fraction = contact_radius*rotation/resultant_slip_speed
    top_tension = bottom_tension + weight*t_z*length + mu*contact*axial_fraction
    top_torque = bottom_torque + mu*contact*radius*rotational_fraction

Midpoint tension/contact iterates to relative tolerance 1e-7 with an 80-iteration bound. Survey/string boundaries are included. Step and half-step runs report changes in surface tension/torque. Friction ± supplied delta runs retain surface ranges. Installed casing IDs and hole coverage/clearance are checked; planned casing is not assumed installed.

Supplied surface limits require provenance; missing and exceeded ratings remain explicit. Observations require sensor/reference notes. Residual is observed minus calculated. No automatic friction fit, calibration, blind-validation or motor/downhole bias correction is claimed. Negative tension is retained as a compression observation with a buckling/stiffness qualification flag.

Analytic tests independently recover vertical buoyant weight in all four motion states, constant-inclination pickup/slackoff/rotating friction, zero-friction curved-path TVD equilibrium, mesh change, compression, rating exceedance and observed residual signs. The vector equilibrium is explicitly documented here; these tests do not claim replication of inaccessible published field datasets.

Open qualification: independently checked field pickup/slackoff/rotating comparisons, state-specific friction calibration with held-out observations, pipe stiffness/buckling/contact, pressure end forces, dynamic loads, component ratings and rig/sensor bias.

## Release interpretation

Working software and analytic/API/browser verification are implementation evidence. They do not confer engineering approval, field accuracy, standards compliance or equipment authority. No new library dependency, cloud connection, live rig interface or control route was added. Native M5 EM inversion and Modules 11–17 remain outside this completed research-build task.
