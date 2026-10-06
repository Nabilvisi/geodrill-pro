"""Standardized study result explanations and lineage provenance (GD-A03).

Provides:
- Complete provenance: source datasets (with SHA-256), exact geometry revision, model version.
- Engineering assumptions, operational applicability envelope, and withholding reasons.
- Human-readable narrative explanation preserved across JSON and export packs.
"""
from typing import Any, TypedDict


class StudyExplanation(TypedDict):
    study_id: str
    model: str
    study_name: str
    created_at: str
    model_version: str
    sources: list[dict[str, Any]]
    geometry_revision: dict[str, Any] | None
    assumptions: list[str]
    applicability: list[str]
    withholding_reasons: list[str]
    is_current: bool
    explanation_text: str


def explain_study(
    calculation: dict[str, Any],
    project: dict[str, Any],
    datasets: list[dict[str, Any]],
    revisions: list[dict[str, Any]],
) -> StudyExplanation:
    """Generate a consistent, structured explanation and provenance record for a study calculation."""
    study_id = calculation.get("id", "unknown")
    model = calculation.get("model", "unknown")
    created_at = calculation.get("created_at", "")
    inputs = calculation.get("inputs_si", {})
    result = calculation.get("result", {})
    study_name = inputs.get("study_name") or f"{model} study ({study_id[:8]})"

    # Datasets index by ID
    ds_by_id = {d["id"]: d for d in datasets}
    # Latest geometry revision
    latest_geom = revisions[0] if revisions else None
    latest_geom_id = latest_geom["id"] if latest_geom else None

    # Identify geometry revision
    calc_geom_id = inputs.get("geometry_revision_id") or result.get("geometry_revision_id")
    geom_info = None
    is_current_geom = True
    if calc_geom_id:
        matching_rev = next((r for r in revisions if r["id"] == calc_geom_id), None)
        is_current_geom = (calc_geom_id == latest_geom_id)
        if matching_rev:
            geom_info = {
                "id": matching_rev["id"],
                "sha256": matching_rev["sha256"],
                "change_note": matching_rev.get("change_note", "Standard revision"),
                "is_current": is_current_geom,
                "created_at": matching_rev.get("created_at", ""),
                "survey_dataset_id": matching_rev.get("input", {}).get("survey_dataset_id"),
            }
        else:
            geom_info = {
                "id": calc_geom_id,
                "sha256": result.get("geometry_sha256", "unknown"),
                "change_note": "Historical geometry revision",
                "is_current": is_current_geom,
                "created_at": "",
                "survey_dataset_id": None,
            }

    # Identify sources
    sources: list[dict[str, Any]] = []
    # 1. Survey source from geometry
    if geom_info and geom_info.get("survey_dataset_id"):
        survey_ds = ds_by_id.get(geom_info["survey_dataset_id"])
        if survey_ds:
            sources.append({
                "kind": "survey",
                "dataset_id": survey_ds["id"],
                "filename": survey_ds["filename"],
                "sha256": survey_ds["source_hash"],
                "role": "directional_trajectory"
            })
    elif result.get("survey_source_sha256"):
        sources.append({
            "kind": "survey",
            "dataset_id": "bound_via_geometry",
            "filename": result.get("survey_filename", "survey_source.csv"),
            "sha256": result.get("survey_source_sha256"),
            "role": "directional_trajectory"
        })

    # 2. Input dataset (e.g. LAS, research document)
    for ds_key in ("dataset_id", "input_dataset_id"):
        if inputs.get(ds_key):
            ds_id = inputs[ds_key]
            ds = ds_by_id.get(ds_id)
            if ds:
                sources.append({
                    "kind": ds.get("kind", "data"),
                    "dataset_id": ds["id"],
                    "filename": ds["filename"],
                    "sha256": ds["source_hash"],
                    "role": "study_source_input"
                })
            elif result.get(f"{ds_key}_sha256") or result.get("source_sha256"):
                sources.append({
                    "kind": "input_document",
                    "dataset_id": ds_id,
                    "filename": result.get("input_document_filename", "input.json"),
                    "sha256": result.get("source_sha256") or result.get("input_document_sha256", ""),
                    "role": "study_source_input"
                })

    # 3. Linked studies
    for link_key in ("hydraulics_calculation_id", "torque_drag_calculation_id"):
        if inputs.get(link_key):
            sources.append({
                "kind": "linked_calculation",
                "dataset_id": inputs[link_key],
                "filename": f"{link_key}:{inputs[link_key][:8]}",
                "sha256": result.get(link_key.replace("_calculation_id", "_sha256"), "linked_provenance"),
                "role": link_key
            })

    # Model version
    model_version = result.get("model_version", "0.8.0")

    # Assumptions extraction
    assumptions: list[str] = [
        f"Project well: '{project.get('well_name', 'Default')}', origin: '{project.get('origin', 'synthetic')}'",
        f"Datum: '{project.get('datum', 'Rig Floor RKB')}', North reference: '{project.get('north_reference', 'grid')}'"
    ]
    if "bit_diameter_m" in project:
        assumptions.append(f"Nominal bit diameter: {project['bit_diameter_m']} m")

    if model in ("casing", "casing-envelopes"):
        assumptions.append("API TR 5C3 / ISO 10400 casing burst, collapse, and axial load ratings (yield/plastic/transition/elastic collapse; Barlow burst).")
        if model == "casing-envelopes":
            assumptions.append("Full well profile operational load lines: burst kick, evacuation collapse, thermal expansion (APB), and running overpull.")
    elif model == "hydraulics":
        mud = inputs.get("mud", {})
        assumptions.append(f"Mud rheology model: '{mud.get('rheology', 'herschel_bulkley')}', base density: {mud.get('density_kg_m3')} kg/m³")
        assumptions.append("Annular flow concentric approximation; steady-state incompressible hydraulics.")
    elif model == "torque-drag":
        drag_model = inputs.get("model", "soft_string").replace("_", "-")
        assumptions.append(f"{drag_model.title()} formulation with friction factors")
    elif model == "clustering" or model == "shaly_sand":
        assumptions.append("Petrophysical evaluation assumes calibrated wireline/LWD log responses aligned to project depth datum.")
    else:
        evidence_state = inputs.get("evidence_state") or result.get("input_evidence_state", "unspecified")
        assumptions.append(f"Input evidence classification: '{evidence_state}'")

    # Applicability envelope
    applicability: list[str] = [
        "Engineering study for pre-drill planning and operational scenario review.",
        "Deterministic mathematical modeling; equipment control and autonomous rig commands strictly excluded.",
    ]
    if result.get("total_depth_md_m"):
        applicability.append(f"Valid over trajectory interval 0.0 m to {round(result['total_depth_md_m'], 2)} m MD.")
    elif inputs.get("depth_m"):
        applicability.append(f"Evaluated at target depth {inputs.get('depth_m')} m MD.")

    # Withholding reasons
    withholding_reasons: list[str] = []
    if not is_current_geom:
        withholding_reasons.append(
            f"Stale Geometry: Study was computed against geometry revision {calc_geom_id[:8]}, which has been superseded by revision {latest_geom_id[:8]}."
        )

    if project.get("origin") != "synthetic" and inputs.get("evidence_state") == "synthetic":
        withholding_reasons.append("Caution: Synthetic evidence input applied in a non-synthetic project context.")

    if result.get("withheld"):
        withholding_reasons.append(f"Study result explicitly withheld: {result.get('withholding_reason', 'Criteria not satisfied')}")

    if result.get("integrity_verification", {}).get("reasons"):
        for r in result["integrity_verification"]["reasons"]:
            withholding_reasons.append(f"Casing integrity withholding: {r}")

    is_current = (len(withholding_reasons) == 0 and is_current_geom)

    # Narrative explanation
    narrative_lines = [
        f"### Study Explanation: {study_name}",
        f"- **Model**: `{model}` (v{model_version})",
        f"- **Executed At**: {created_at}",
        f"- **Status**: {'Current & Verified' if is_current else 'Superseded / Stale / Caution'}",
        "",
        "#### Provenance & Sources",
    ]
    if sources:
        for s in sources:
            narrative_lines.append(f"- **{s['kind'].title()}**: `{s['filename']}` (SHA-256: `{s['sha256'][:16]}...`) - Role: {s['role']}")
    else:
        narrative_lines.append("- *No external source datasets bound directly.*")

    if geom_info:
        narrative_lines.append(
            f"- **Geometry Revision**: `{geom_info['id'][:8]}` ({geom_info['change_note']}) "
            f"[{'CURRENT' if geom_info['is_current'] else 'SUPERSEDED'}]"
        )

    narrative_lines.append("")
    narrative_lines.append("#### Engineering Assumptions")
    for a in assumptions:
        narrative_lines.append(f"- {a}")

    narrative_lines.append("")
    narrative_lines.append("#### Applicability Envelope")
    for app in applicability:
        narrative_lines.append(f"- {app}")

    if withholding_reasons:
        narrative_lines.append("")
        narrative_lines.append("#### Withholding Reasons & Cautions")
        for wr in withholding_reasons:
            narrative_lines.append(f"- [WARNING] {wr}")

    explanation_text = "\n".join(narrative_lines)

    return {
        "study_id": study_id,
        "model": model,
        "study_name": study_name,
        "created_at": created_at,
        "model_version": model_version,
        "sources": sources,
        "geometry_revision": geom_info,
        "assumptions": assumptions,
        "applicability": applicability,
        "withholding_reasons": withholding_reasons,
        "is_current": is_current,
        "explanation_text": explanation_text,
    }
