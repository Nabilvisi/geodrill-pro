import csv
import io
import math
from datetime import datetime, timedelta, timezone


def telemetry():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "md[m]", "tvd[m]", "wob[kN]", "torque[kN.m]", "rpm[rpm]", "rop[m/h]", "spp[MPa]", "flow[L/min]", "state"])
    start = datetime(2026, 1, 15, 8, 0, tzinfo=timezone.utc)
    for i in range(240):
        connection = 90 <= i <= 96
        writer.writerow([(start + timedelta(seconds=i * 2 + (24 if i >= 170 else 0))).isoformat(),
                         round(2840 + i * 0.018, 3), round(2400 + i * 0.007, 3),
                         round(108 + 8 * math.sin(i / 14), 3), round(8 + math.sin(i / 17) + (1.8 if 130 < i < 155 else 0), 3),
                         0 if connection else round(122 + 4 * math.sin(i / 13), 2),
                         0 if connection or i == 190 else round(27 + 4 * math.sin(i / 20), 2),
                         "" if i == 42 else round(21 + 0.9 * math.sin(i / 22), 3),
                         0 if connection else round(1850 + 35 * math.sin(i / 12), 2), "connection" if connection else "drilling"])
    return output.getvalue().encode()


SURVEY = b"md[m],inclination[deg],azimuth[deg]\n0,0,35\n500,0,35\n900,12,35\n1300,26,40\n1700,38,45\n2100,44,48\n2500,48,50\n2850,50,52\n"
LAS = b"""~Version Information
VERS. 2.0 : LAS version
WRAP. NO : unwrapped
~Well Information
NULL. -999.25 : null
~Curve Information
DEPT.M : measured depth
GR.API : gamma ray
RHOB.G/C3 : bulk density
~ASCII
2400 45 2.45
2401 48 2.46
2402 -999.25 2.44
2403 76 2.51
2404 92 2.55
"""

def shaly_sand():
    """Native-depth synthetic PHIT/VSH with labelled software test cases."""
    cases=[(0.,.30),(.30,.045),(.70,.405),(.40,.24),(.46,.189),(.50,.315),(.24,.266),(1.,.15),(.90,.40),(.25,None)]
    header="~Version\nVERS. 2.0\nWRAP. NO\n~Well\nNULL. -999.25\n~Curve\nDEPT.M\nVSH.V/V\nPHIT.V/V\nGR.API\n~ASCII\n"
    return (header+"".join(f"{2400+i} {v} {phi if phi is not None else -999.25} {20+80*v}\n" for i,(v,phi) in enumerate(cases))).encode()

def em_vendor(well_name, datum):
    import json
    samples=[]
    for i in range(8):
        quality="vendor_usable" if i<6 else "vendor_rejected" if i==6 else "unknown"
        rh=10.+i*2. if i!=3 else None
        samples.append({
            "md_m":100.+i*10.,"acquired_at":f"2026-01-01T00:0{i}:00Z",
            "received_at":f"2026-01-01T00:0{i}:12Z" if i!=4 else None,
            "rh_ohm_m":rh,"rv_ohm_m":rh*1.5 if rh else None,
            "rh_interval":{"lower":rh*.8,"upper":rh*1.2,"meaning":"Synthetic parameter range; not calibrated confidence"} if rh and i!=5 else None,
            "rv_interval":None,"quality":quality,"quality_note":"Generated example; no physical instrument",
            "boundary_distance_m":5.-i if i!=3 else None,
            "boundary_reference":"Synthetic signed normal distance from measurement point; positive toward labelled upper bed" if i!=3 else None,
            "boundary_interval":{"lower":3.-i,"upper":7.-i,"meaning":"Generated range; no field evidence"} if i!=3 else None,
            "misfit":None,"misfit_definition":None,
        })
    value={"schema_version":"geodrill-em-vendor-1","origin":"synthetic",
           "well_name":well_name,"depth_datum":datum,"resistivity_unit":"ohm.m","boundary_distance_unit":"m",
           "source_reference":"Generated software example; not a vendor or field inversion",
           "data_rights_note":"Local synthetic software reference",
           "tool":{"vendor":"Synthetic example","tool":"No physical EM tool","processing_version":"example-1",
                   "frequencies_hz":[],"transmitter_receiver_spacings_m":[],
                   "geometry_orientation_note":"Not supplied; no instrument",
                   "tool_to_bit_offset_m":None,"model_dimension":"unknown",
                   "forward_model_reference":"Not supplied; generated interpretations only",
                   "calibration_environment_note":"No measurement, mud, borehole or calibration evidence",
                   "priors_regularization_note":"No inverse solve; synthetic values for import/review testing",
                   "uncertainty_nonuniqueness_note":"Example ranges only; no calibrated confidence or unique earth model",
                   "qualification_reference":None},
           "samples":samples}
    return json.dumps(value,indent=2,allow_nan=False).encode("utf-8")

def hydraulics_example(revision):
    import math
    samples=revision["result"]["samples"]
    selected=samples[::max(1,math.ceil(len(samples)/80))]
    if selected[-1]["md_m"]!=samples[-1]["md_m"]:
        selected.append(samples[-1])
    td=samples[-1]["md_m"]
    return {
        "study_name":"Synthetic steady HB circulation","geometry_revision_id":revision["id"],"depth_datum":revision["input"]["datum"],
        "scenario_at":"2026-01-01T12:00:00Z","maximum_mud_age_hours":24.,
        "mud":{"density_kg_m3":1200.,"rheology":"herschel_bulkley","consistency_pa_sn":.2,"flow_index":.7,"yield_stress_pa":3.,
               "measured_at":"2026-01-01T00:00:00Z","evidence_state":"synthetic",
               "source_note":"Generated software fluid; not a measured mud",
               "test_temperature_c":20.,"density_rheology_basis_note":"Synthetic constant density/rheology; no temperature or pressure corrections"},
        "circulation_state":"steady_single_phase","flow_regime":"supplied_laminar",
        "applicability_note":"Synthetic stationary concentric laminar scenario; no flow-loop/PWD qualification",
        "geometry_state":"include_planned_scenario",
        "string_sections":[{"name":"Synthetic pipe","top_md_m":0.,"bottom_md_m":td,"outside_diameter_m":.127,"inside_diameter_m":.108,"source_note":"Generated nominal pipe dimensions; no tool joints"}],
        "flow_m3_s":.001,"surface_backpressure_pa":100000.,"surface_loss_pa":10000.,
        "surface_loss_note":"Synthetic upstream supply loss at this scenario; fixed across flow sensitivity",
        "nozzle_total_area_m2":.0003,"nozzle_discharge_coefficient":.95,"nozzle_source_note":"Synthetic equivalent nozzle area and coefficient",
        "rotation_rad_s":0.,"eccentricity_fraction":0.,"cuttings_volume_fraction":0.,"wall_roughness_m":0.,
        "pressure_window":{"reference":"surface_atmospheric_gauge","interpolation":"piecewise_linear_md","evidence_state":"synthetic",
                           "source_note":"Generated MD knots from saved TVD; not PP/FG measurements",
                           "review_note":"Software example only; no operational pressure limits",
                           "knots":[{"md_m":p["md_m"],"pore_gauge_pa":max(0.,p["tvd_m"])*6000.,
                                     "fracture_gauge_pa":1e6+max(0.,p["tvd_m"])*16000.,"pore_upper_allowance_pa":0.,"fracture_lower_allowance_pa":0.} for p in selected]},
        "surface_rating_pa":50e6,"surface_rating_source":"Generated surface-supply rating; not manufacturer evidence",
        "sensitivity":{"density_delta_kg_m3":20.,"flow_delta_m3_s":.0001,"consistency_relative_delta":.1,"backpressure_delta_pa":10000.}}


def research_template(model,revision,origin):
    if model in ("dynamics","bit-condition","wear-fatigue","anomaly","gas-phase","supervision"):
        from .late_demo import late_template
        return late_template(model,revision,origin)
    td=revision["result"]["total_depth_md_m"]
    base={"study_name":"Synthetic "+model+" scenario" if origin=="synthetic" else "Draft "+model+" scenario",
          "geometry_revision_id":revision["id"],"depth_datum":revision["input"]["datum"],
          "evidence_state":"synthetic" if origin=="synthetic" else "unknown",
          "source_note":"Generated software assumptions; no field qualification" if origin=="synthetic" else "Replace draft assumptions with traceable evidence"}
    if model=="offset-benchmarking":
        import hashlib,json
        records=[]
        if origin=="synthetic":
            for i,hours in enumerate((40.,50.,60.),1):
                record={"well_id":f"SYN-OFFSET-{i}","well_name":f"Synthetic offset {i}",
                        "field_name":"Generated demonstration field","hole_diameter_m":.3,
                        "bit_family":"Synthetic PDC","formation":"Synthetic sand","trajectory_type":"vertical",
                        "spud_date":"2026-01-01","drilled_interval_m":1000.,"drilling_hours":hours,
                        "npt_hours":10.,"total_cost":1e6+i*100000,"cost_currency":"USD",
                        "is_adjudicated":True,"adjudication_note":"Synthetic classification fixture; no actual reviewer approval"}
                record["evidence_source_hash"]=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
                records.append(record)
        return {**base,"planned_interval_m":min(td,1000.),"criteria":{"target_hole_diameter_m":.3,
                "target_formation":"Synthetic sand" if origin=="synthetic" else "Replace with target formation",
                "target_bit_family":None,"target_trajectory_type":None,"max_hole_diameter_diff_m":.0254,
                "require_adjudicated_only":True},"offset_wells":records,
                "planned_rig_rate_per_day":100000.,"cost_currency":"USD"}
    if model=="geomechanics":
        import hashlib,json,math
        z=revision["result"]["samples"][-1]["tvd_m"]
        core={"specimen_id":"SYN-CORE","confining_pressure_pa":20e6,"peak_axial_stress_pa":85e6,
              "pore_pressure_pa":10e6,"cohesion_pa":12e6,"friction_angle_deg":30.,
              "unconfined_compressive_strength_pa":24e6*math.sqrt(3),"tensile_strength_pa":4e6,
              "youngs_modulus_pa":25e9,"poissons_ratio":.22,"biot_coefficient":.85,
              "test_standard":"Generated analytical fixture","certificate_id":"SYN-NO-ACTUAL-CERTIFICATE"}
        core["source_sha256"]=hashlib.sha256(json.dumps(core,sort_keys=True).encode()).hexdigest()
        calibration={"method":"XLOT","measured_shmin_gradient_sg":1.65,"test_depth_tvd_m":max(z,.001),
                     "closure_pressure_gauge_pa":1.65*1000*9.80665*max(z,.001),"pressure_reference":"at_test_depth",
                     "calibration_quality":"verified_closure","evidence_note":"Generated closure-state fixture; no actual reviewer or field test"}
        calibration["source_sha256"]=hashlib.sha256(json.dumps(calibration,sort_keys=True).encode()).hexdigest()
        return {**base,"md_m":td,"azimuth_shmax_deg":0.,"stress_north_reference":revision["result"].get("north_reference","true"),"overburden_gradient_sg":2.3,"pore_pressure_sg":1.1,
                "tectonic_strain_x":0.,"tectonic_strain_y":min(.01,.0003*max(z,0)/1000),
                "core_test":core if origin=="synthetic" else None,"stress_calibration":calibration if origin=="synthetic" else None,
                "surface_temperature_c":15.,"geothermal_gradient_c_per_100m":3.,"base_mud_density_sg":1.5,
                "mud_compressibility_per_pa":4e-10,"mud_thermal_expansion_per_c":6e-4,
                "shear_failure_model":"mogi_coulomb","minimum_tested_pressure_sg":.8,"maximum_tested_pressure_sg":3.5}
    if model=="stability":
        return {**base,"md_m":min(td,1000.),"model":"isotropic_elastic_impermeable",
                "stress_north_pa":22e6,"stress_east_pa":13e6,"stress_vertical_pa":25e6,
                "stress_ne_pa":0.,"stress_nv_pa":0.,"stress_ev_pa":0.,"pore_pressure_pa":10e6,"wall_pressure_pa":10e6,
                "young_modulus_pa":20e9,"poisson_ratio":.25,"expansion_per_k":1e-5,"delta_temperature_k":-20.,
                "thermal_scope":"restrained_wall_estimate","ucs_pa":40e6,"tensile_strength_pa":2e6,"friction_angle_deg":30.,
                "pressure_basis_note":"Supplied gauge pressures share the stress reference; perfect impermeable wall",
                "external_lower_pa":None,"external_upper_pa":None,"external_bounds_state":"none","external_bounds_note":None}
    if model=="transport":
        return {**base,"hydraulics_calculation_id":"","particle_diameter_m":.0001,"particle_density_kg_m3":2600.,"shape":"sphere",
                "rop_m_s":.00001,"duration_s":3600.,"generation_stop_s":1800.,"initial_volume_fraction":0.,"rotation_rad_s":0.,"time_step_s":30.}
    if model=="surge-swab":
        holes=revision["input"]["hole_sections"]
        interval=holes[0] if holes else {"top_md_m":0.,"bottom_md_m":td}
        return {**base,"hydraulics_calculation_id":"","top_md_m":interval["top_md_m"],"bottom_md_m":interval["bottom_md_m"],
                "wave_speed_m_s":800.,"wave_speed_note":"Supplied synthetic effective acoustic wave speed",
                "displacement":"closed_end_piston","motion":[{"time_s":0.,"downward_speed_m_s":0.},
                {"time_s":2.,"downward_speed_m_s":.05},{"time_s":6.,"downward_speed_m_s":.05},
                {"time_s":8.,"downward_speed_m_s":0.},{"time_s":12.,"downward_speed_m_s":0.}],
                "cells":20,"convergence_tolerance_pa":50000.}
    if model=="buckling":
        return {**base,"torque_drag_calculation_id":"unselected","top_md_m":0.,"bottom_md_m":td,
                "young_modulus_pa":207e9,"stiffness_note":"Generated nominal steel modulus; verify material and temperature",
                "boundary":"long_unrestrained_rotation","boundary_note":"Research long-pipe approximation; verify end restraint",
                "pipe_configuration":"uniform_plain_pipe","force_basis":"m10_effective_baseline",
                "force_basis_note":"M10 buoyed effective-force baseline, no additional pressure correction",
                "wall_loads":[],"compression_allowance_n":1000.,"modulus_relative_delta":.05,
                "clearance_relative_delta":.05,"friction_delta":.02,"transfer_model":"screen_only",
                "integration_cells":128,"transfer_tolerance_n":100.}
    return {**base,"fluid_density_kg_m3":1200.,"string_sections":[{"name":"Draft pipe","top_md_m":0.,"bottom_md_m":td,
            "outside_diameter_m":.127,"inside_diameter_m":.108,"material_density_kg_m3":7850.,"friction_coefficient":.2}],
            "operation":"pickup","axial_speed_m_s":.1,"rotation_rad_s":0.,"bottom_tension_n":0.,"bottom_torque_nm":0.,"step_m":10.,
            "friction_delta":.05,"surface_tension_limit_n":None,"surface_torque_limit_nm":None,"rating_note":None,
            "observed_hookload_n":None,"observed_torque_nm":None,"observation_note":None}
