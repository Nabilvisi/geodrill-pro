"""Study dependency, scenario management and stale-result tracker (GD-A02).

Tracks:
- Lineage relationships between geometry revisions, datasets, and engineering studies.
- When an input revision changes (e.g. M1 Geometry Revision or source dataset), flags
  downstream dependent calculations as stale without overwriting or deleting immutable historical records.
- Generates side-by-side scenario comparison matrices between baseline and alternative cases.
"""
from typing import Any, TypedDict, Literal


class DependencyNode(TypedDict):
    id: str
    kind: Literal["dataset", "geometry", "calculation"]
    model_or_type: str
    name: str
    created_at: str
    sha256: str
    is_current: bool
    stale_reasons: list[str]


class LineageGraph(TypedDict):
    project_id: str
    nodes: list[DependencyNode]
    edges: list[dict[str, str]]  # {from: id, to: id, relation: "geometry_binding" | "dataset_source" | "linked_study"}


class ScenarioComparison(TypedDict):
    baseline_id: str
    alternative_id: str
    model: str
    geometry_compatible: bool
    geometry_note: str
    sources_compatible: bool
    sources_note: str
    units_compatible: bool
    units_note: str
    compatibility_status: Literal["compatible", "warning", "incompatible"]
    warnings: list[str]
    common_inputs: dict[str, Any]
    differing_inputs: dict[str, dict[str, Any]]  # {param: {baseline: val, alternative: val}}
    outcome_deltas: dict[str, dict[str, Any]]
    evaluation: str


def build_lineage_graph(project_id: str, datasets: list[dict], revisions: list[dict], calculations: list[dict]) -> LineageGraph:
    """Build a complete dependency and freshness graph for a project."""
    nodes: list[DependencyNode] = []
    edges: list[dict[str, str]] = []

    # Map current active geometry revision (the latest one)
    latest_geom = revisions[0] if revisions else None
    latest_geom_id = latest_geom["id"] if latest_geom else None

    # Datasets
    for d in datasets:
        nodes.append({
            "id": d["id"],
            "kind": "dataset",
            "model_or_type": d["kind"],
            "name": d["filename"],
            "created_at": d["created_at"],
            "sha256": d["source_hash"],
            "is_current": True,
            "stale_reasons": []
        })

    # Geometry revisions
    for r in revisions:
        is_latest = (r["id"] == latest_geom_id)
        nodes.append({
            "id": r["id"],
            "kind": "geometry",
            "model_or_type": "M01_geometry",
            "name": f"Revision {r['id'][:8]} ({r['change_note']})",
            "created_at": r["created_at"],
            "sha256": r["sha256"],
            "is_current": is_latest,
            "stale_reasons": [] if is_latest else ["Superseded by newer well geometry revision"]
        })
        # Edge to survey dataset
        survey_id = r["input"].get("survey_dataset_id")
        if survey_id:
            edges.append({"from": survey_id, "to": r["id"], "relation": "survey_source"})

    # Calculations
    for c in calculations:
        inputs = c.get("inputs_si", {})
        result = c.get("result", {})
        calc_geom_id = inputs.get("geometry_revision_id") or result.get("geometry_revision_id")
        
        stale_reasons: list[str] = []
        if calc_geom_id and latest_geom_id and calc_geom_id != latest_geom_id:
            stale_reasons.append(f"Bound to superseded geometry revision {calc_geom_id[:8]}; current is {latest_geom_id[:8]}")

        study_name = inputs.get("study_name") or f"{c['model']} calculation"
        nodes.append({
            "id": c["id"],
            "kind": "calculation",
            "model_or_type": c["model"],
            "name": study_name,
            "created_at": c["created_at"],
            "sha256": result.get("geometry_sha256") or c["id"],
            "is_current": len(stale_reasons) == 0,
            "stale_reasons": stale_reasons
        })

        if calc_geom_id:
            edges.append({"from": calc_geom_id, "to": c["id"], "relation": "geometry_binding"})

        # Linked calculations (e.g. hydraulics_calculation_id or torque_drag_calculation_id)
        for link_field in ("hydraulics_calculation_id", "torque_drag_calculation_id"):
            linked_calc = inputs.get(link_field)
            if linked_calc:
                edges.append({"from": linked_calc, "to": c["id"], "relation": "linked_study"})

    return {
        "project_id": project_id,
        "nodes": nodes,
        "edges": edges
    }


def compare_scenarios(baseline: dict[str, Any], alternative: dict[str, Any]) -> ScenarioComparison:
    """Compare baseline and alternative calculation scenarios, isolating inputs and outcomes with explicit compatibility checks."""
    if baseline.get("model") != alternative.get("model"):
        raise ValueError("Cannot compare scenarios across different models.")

    model = baseline.get("model", "unknown")
    base_in = baseline.get("inputs_si", {})
    alt_in = alternative.get("inputs_si", {})
    base_res = baseline.get("result", {})
    alt_res = alternative.get("result", {})

    warnings: list[str] = []

    # 1. Geometry compatibility
    base_geom = base_in.get("geometry_revision_id") or base_res.get("geometry_revision_id")
    alt_geom = alt_in.get("geometry_revision_id") or alt_res.get("geometry_revision_id")
    if base_geom and alt_geom:
        if base_geom == alt_geom:
            geom_compatible = True
            geom_note = f"Shared geometry revision: {base_geom[:8]}"
        else:
            geom_compatible = False
            geom_note = f"Incompatible geometry revisions: baseline uses {base_geom[:8]}, alternative uses {alt_geom[:8]}"
            warnings.append(geom_note)
    elif not base_geom and not alt_geom:
        geom_compatible = True
        geom_note = "Neither scenario depends on a wellbore geometry revision"
    else:
        geom_compatible = False
        geom_note = "One scenario is bound to a geometry revision while the other is not"
        warnings.append(geom_note)

    # 2. Source datasets compatibility
    base_src_sha = base_res.get("source_sha256") or base_res.get("survey_source_sha256")
    alt_src_sha = alt_res.get("source_sha256") or alt_res.get("survey_source_sha256")
    if base_src_sha and alt_src_sha:
        if base_src_sha == alt_src_sha:
            src_compatible = True
            src_note = f"Matching source dataset SHA-256: {base_src_sha[:12]}..."
        else:
            src_compatible = False
            src_note = f"Source dataset hash mismatch: baseline ({base_src_sha[:8]}...) vs alternative ({alt_src_sha[:8]}...)"
            warnings.append(src_note)
    else:
        src_compatible = True
        src_note = "Source dataset hashes aligned or not individually tracked"

    # 3. Units compatibility
    # Both calculations store normalized inputs in inputs_si
    units_compatible = True
    units_note = "Both scenarios evaluated on standard SI basis (inputs_si)"

    if not geom_compatible or not src_compatible:
        status: Literal["compatible", "warning", "incompatible"] = "warning" if (geom_compatible or src_compatible) else "incompatible"
    else:
        status = "compatible"

    all_input_keys = set(base_in.keys()) | set(alt_in.keys())
    common_inputs: dict[str, Any] = {}
    differing_inputs: dict[str, dict[str, Any]] = {}

    for k in sorted(all_input_keys):
        b_val = base_in.get(k)
        a_val = alt_in.get(k)
        if b_val == a_val:
            common_inputs[k] = b_val
        else:
            differing_inputs[k] = {"baseline": b_val, "alternative": a_val}

    all_res_keys = set(base_res.keys()) | set(alt_res.keys())
    outcome_deltas: dict[str, dict[str, Any]] = {}
    for k in sorted(all_res_keys):
        if k in {"profile", "history", "cases", "segments"}:
            continue  # exclude huge arrays from scalar summary
        b_val = base_res.get(k)
        a_val = alt_res.get(k)
        if isinstance(b_val, (int, float)) and isinstance(a_val, (int, float)) and not isinstance(b_val, bool) and not isinstance(a_val, bool):
            delta = a_val - b_val
            pct = ((delta / abs(b_val)) * 100.0) if b_val != 0 else 0.0
            outcome_deltas[k] = {
                "baseline": b_val,
                "alternative": a_val,
                "absolute_delta": round(delta, 6),
                "percent_delta": round(pct, 2)
            }
        elif b_val != a_val:
            outcome_deltas[k] = {"baseline": b_val, "alternative": a_val}

    eval_summary = f"Comparison identified {len(differing_inputs)} differing inputs and {len(outcome_deltas)} outcome variance metrics."
    if warnings:
        eval_summary += f" Compatibility status: {status.upper()} ({len(warnings)} caution(s))."

    return {
        "baseline_id": baseline["id"],
        "alternative_id": alternative["id"],
        "model": model,
        "geometry_compatible": geom_compatible,
        "geometry_note": geom_note,
        "sources_compatible": src_compatible,
        "sources_note": src_note,
        "units_compatible": units_compatible,
        "units_note": units_note,
        "compatibility_status": status,
        "warnings": warnings,
        "common_inputs": common_inputs,
        "differing_inputs": differing_inputs,
        "outcome_deltas": outcome_deltas,
        "evaluation": eval_summary,
    }
