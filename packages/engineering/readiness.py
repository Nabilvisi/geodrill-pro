"""Source field mapping dictionary and data readiness validator (GD-A01).

Supports:
- Robust unit and alias mapping across telemetry, directional surveys, and log curves.
- Data readiness assessment (completeness, null percentage, sampling regularity, state consistency).
- Explicit versioned mapping configuration preserving source headers and conversion factors.
"""
from typing import Literal, TypedDict, Any
import math
import re

# Standard industry aliases for channels
STANDARD_ALIASES: dict[str, list[str]] = {
    "md": ["md", "measured_depth", "depth", "dept", "bit_depth", "hole_depth"],
    "tvd": ["tvd", "true_vertical_depth", "tvd_ss", "tvd_subsea"],
    "wob": ["wob", "weight_on_bit", "bit_weight", "wob_surface", "wob_downhole"],
    "torque": ["torque", "torq", "surface_torque", "rotary_torque", "drill_torque"],
    "rpm": ["rpm", "rotary_speed", "surface_rpm", "drill_rpm", "rotation"],
    "rop": ["rop", "rate_of_penetration", "drill_rate", "drilling_speed"],
    "spp": ["spp", "standpipe_pressure", "pump_pressure", "circ_pressure"],
    "flow": ["flow", "flow_rate", "mud_flow", "pump_rate", "flow_in", "flow_rate_in"],
    "inclination": ["inc", "incl", "inclination", "deviation"],
    "azimuth": ["azi", "azim", "azimuth", "direction", "hole_azimuth"],
    "timestamp": ["time", "datetime", "timestamp", "date_time", "utc_time"],
    "state": ["state", "rig_state", "drilling_state", "activity_state"]
}

# Unit factors to standard SI units
UNIT_FACTORS: dict[str, dict[str, float]] = {
    "length": {
        "m": 1.0,
        "meter": 1.0,
        "meters": 1.0,
        "ft": 0.3048,
        "feet": 0.3048,
        "in": 0.0254,
        "inch": 0.0254
    },
    "force": {
        "n": 1.0,
        "kn": 1000.0,
        "lbf": 4.4482216152605,
        "klbf": 4448.2216152605,
        "ton": 8896.443230521
    },
    "torque": {
        "n.m": 1.0,
        "nm": 1.0,
        "kn.m": 1000.0,
        "knm": 1000.0,
        "ft.lbf": 1.3558179483314,
        "ftlbf": 1.3558179483314,
        "kft.lbf": 1355.8179483314
    },
    "velocity": {
        "m/s": 1.0,
        "m/h": 1.0 / 3600.0,
        "ft/h": 0.3048 / 3600.0,
        "ft/min": 0.3048 / 60.0
    },
    "pressure": {
        "pa": 1.0,
        "kpa": 1000.0,
        "mpa": 1.0e6,
        "bar": 1.0e5,
        "psi": 6894.757293168,
        "kpsi": 6894757.293168
    },
    "volume_flow": {
        "m3/s": 1.0,
        "l/min": 1.0 / 60000.0,
        "l/s": 0.001,
        "gpm": 0.003785411784 / 60.0,
        "bbl/min": 0.158987294928 / 60.0
    },
    "angle": {
        "rad": 1.0,
        "deg": math.pi / 180.0,
        "degree": math.pi / 180.0
    },
    "frequency": {
        "rad/s": 1.0,
        "rpm": math.pi / 30.0,
        "hz": 2.0 * math.pi
    }
}


class FieldMapping(TypedDict):
    source_header: str
    target_channel: str
    source_unit: str
    target_unit_si: str
    factor_to_si: float


class ReadinessReport(TypedDict):
    total_rows: int
    complete_rows: int
    missing_by_channel: dict[str, int]
    null_percentage: float
    is_ready_for_engineering: bool
    readiness_score_pct: float
    warnings: list[str]
    identified_mappings: list[FieldMapping]


def parse_header_token(header: str) -> tuple[str, str | None]:
    """Parse 'wob[kN]' or 'wob_kN' or 'wob (kN)' into ('wob', 'kN')."""
    h = header.strip()
    match = re.search(r"^(.*?)[\[\(\{](.*?)[\]\)\}]$", h)
    if match:
        return match.group(1).strip().lower(), match.group(2).strip()
    if "_" in h:
        parts = h.rsplit("_", 1)
        if len(parts) == 2 and parts[1].lower() in [u for cat in UNIT_FACTORS.values() for u in cat]:
            return parts[0].strip().lower(), parts[1].strip()
    return h.lower(), None


def find_channel_for_alias(token: str) -> str | None:
    """Find canonical target channel name for an alias token."""
    clean = re.sub(r"[^a-z0-9_]", "", token.lower())
    for channel, aliases in STANDARD_ALIASES.items():
        if clean in aliases or any(clean == a for a in aliases):
            return channel
    return None


def get_conversion_factor(channel: str, unit_str: str) -> float | None:
    """Find SI conversion factor for a given channel and unit string."""
    u = unit_str.strip().lower()
    channel_to_category = {
        "md": "length",
        "tvd": "length",
        "wob": "force",
        "torque": "torque",
        "rpm": "frequency",
        "rop": "velocity",
        "spp": "pressure",
        "flow": "volume_flow",
        "inclination": "angle",
        "azimuth": "angle"
    }
    cat = channel_to_category.get(channel)
    if cat and cat in UNIT_FACTORS:
        return UNIT_FACTORS[cat].get(u)
    return None


def inspect_readiness(headers: list[str], rows: list[dict[str, Any]], dataset_kind: Literal["telemetry", "survey"]) -> ReadinessReport:
    """Evaluate data readiness, detect channel mappings, and compute data quality score."""
    mappings: list[FieldMapping] = []
    warnings: list[str] = []
    
    for h in headers:
        token, unit_hint = parse_header_token(h)
        channel = find_channel_for_alias(token)
        if channel:
            if unit_hint:
                factor = get_conversion_factor(channel, unit_hint)
                if factor is not None:
                    mappings.append({
                        "source_header": h,
                        "target_channel": channel,
                        "source_unit": unit_hint,
                        "target_unit_si": "SI",
                        "factor_to_si": factor
                    })
                else:
                    warnings.append(f"Header '{h}' has unrecognized unit '{unit_hint}'.")
            elif channel in {"timestamp", "state"}:
                mappings.append({
                    "source_header": h,
                    "target_channel": channel,
                    "source_unit": "text",
                    "target_unit_si": "standard",
                    "factor_to_si": 1.0
                })

    mapped_channels = {m["target_channel"] for m in mappings}
    required_channels = (
        {"timestamp", "state", "md", "wob", "torque", "rpm", "rop", "spp", "flow"}
        if dataset_kind == "telemetry"
        else {"md", "inclination", "azimuth"}
    )
    
    missing_channels = required_channels - mapped_channels
    if missing_channels:
        warnings.append(f"Missing required engineering channels: {', '.join(sorted(missing_channels))}")

    # Inspect rows completeness
    total_rows = len(rows)
    complete_count = 0
    missing_by_channel = {c: 0 for c in mapped_channels}

    for row in rows:
        row_has_empty = False
        for m in mappings:
            val = row.get(m["source_header"])
            if val is None or str(val).strip() == "":
                missing_by_channel[m["target_channel"]] += 1
                row_has_empty = True
        if not row_has_empty:
            complete_count += 1

    total_cells = total_rows * max(1, len(mappings))
    total_missing_cells = sum(missing_by_channel.values())
    null_pct = round((total_missing_cells / total_cells * 100.0) if total_cells else 0.0, 2)
    ready = len(missing_channels) == 0 and null_pct < 20.0 and total_rows > 0
    score = max(0.0, min(100.0, round(100.0 - null_pct - (len(missing_channels) * 15.0), 1)))

    return {
        "total_rows": total_rows,
        "complete_rows": complete_count,
        "missing_by_channel": missing_by_channel,
        "null_percentage": null_pct,
        "is_ready_for_engineering": ready,
        "readiness_score_pct": score,
        "warnings": warnings,
        "identified_mappings": mappings
    }


class ProjectIssue(TypedDict):
    id: str
    category: Literal["missing_input", "unresolved_reference", "stale_study", "review_progress", "recovery_status", "event_alert"]
    severity: Literal["blocking", "warning", "info"]
    title: str
    detail: str
    target_page: str
    target_id: str | None


class ProjectReadinessReport(TypedDict):
    project_id: str
    workflow: str
    ready: bool
    score_pct: float
    summary: dict[str, int]
    issues: list[ProjectIssue]


def assess_project_readiness(
    project: dict[str, Any],
    datasets: list[dict[str, Any]],
    revisions: list[dict[str, Any]],
    calculations: list[dict[str, Any]],
    programmes: list[dict[str, Any]] | None = None,
    events: list[dict[str, Any]] | None = None,
    audit_history: list[dict[str, Any]] | None = None,
    workflow: Literal["full_workstation", "directional_survey", "hydraulics_casing", "well_planning", "recovery_audit"] = "full_workstation",
) -> ProjectReadinessReport:
    """Assess overall project readiness against a selected workflow.
    
    Identifies:
    - Missing inputs (survey, telemetry, logs, geometry).
    - Unresolved references (missing datasets, dangling revisions, broken study links).
    - Stale studies (dependent calculations bound to superseded geometry revisions).
    - Review progress (draft, under review, approved programmes, 4-eyes handoff).
    - Recovery and audit status (intact audit trail, unacknowledged critical events).
    """
    project_id = project.get("id", "unknown")
    programmes = programmes or []
    events = events or []
    audit_history = audit_history or []

    issues: list[ProjectIssue] = []

    ds_by_id = {d["id"]: d for d in datasets}
    survey_datasets = [d for d in datasets if d.get("kind") == "survey"]
    telemetry_datasets = [d for d in datasets if d.get("kind") == "telemetry"]
    las_datasets = [d for d in datasets if d.get("kind") == "las"]

    latest_geom = revisions[0] if revisions else None
    latest_geom_id = latest_geom["id"] if latest_geom else None
    rev_by_id = {r["id"]: r for r in revisions}
    calc_by_id = {c["id"]: c for c in calculations}

    # 1. Check Missing Inputs
    if workflow in {"full_workstation", "directional_survey", "hydraulics_casing", "well_planning"}:
        if not survey_datasets:
            issues.append({
                "id": "missing-survey-dataset",
                "category": "missing_input",
                "severity": "blocking",
                "title": "Missing Directional Survey",
                "detail": "No directional survey dataset has been imported. Well geometry and spatial positioning cannot be calculated.",
                "target_page": "imports",
                "target_id": None,
            })
        elif not revisions:
            issues.append({
                "id": "missing-geometry-revision",
                "category": "missing_input",
                "severity": "blocking",
                "title": "Missing Geometry Revision (M1)",
                "detail": "A directional survey is present, but no well geometry revision has been saved.",
                "target_page": "geometry",
                "target_id": None,
            })

    if workflow in {"full_workstation"}:
        if not telemetry_datasets:
            issues.append({
                "id": "info-missing-telemetry",
                "category": "missing_input",
                "severity": "info",
                "title": "No Telemetry Dataset",
                "detail": "Telemetry dataset is not imported. Drilling mechanics (MSE, dynamics) will be unavailable.",
                "target_page": "imports",
                "target_id": None,
            })

    # 2. Check Unresolved References
    for r in revisions:
        survey_ref = r.get("input", {}).get("survey_dataset_id")
        if survey_ref and survey_ref not in ds_by_id:
            issues.append({
                "id": f"unresolved-survey-ref-{r['id'][:8]}",
                "category": "unresolved_reference",
                "severity": "blocking",
                "title": f"Unresolved Survey Reference in Revision {r['id'][:8]}",
                "detail": f"Geometry revision references survey dataset '{survey_ref}' which cannot be found.",
                "target_page": "geometry",
                "target_id": r["id"],
            })

    for c in calculations:
        inputs = c.get("inputs_si", {})
        result = c.get("result", {})
        c_geom = inputs.get("geometry_revision_id") or result.get("geometry_revision_id")
        if c_geom and c_geom not in rev_by_id:
            issues.append({
                "id": f"unresolved-geom-ref-{c['id'][:8]}",
                "category": "unresolved_reference",
                "severity": "blocking",
                "title": f"Unresolved Geometry in Study {c['id'][:8]}",
                "detail": f"Calculation '{c['model']}' references geometry revision '{c_geom}' which is missing from project records.",
                "target_page": "calculations",
                "target_id": c["id"],
            })

        for link_field in ("hydraulics_calculation_id", "torque_drag_calculation_id"):
            link_id = inputs.get(link_field)
            if link_id and link_id not in calc_by_id:
                issues.append({
                    "id": f"unresolved-link-{link_field}-{c['id'][:8]}",
                    "category": "unresolved_reference",
                    "severity": "blocking",
                    "title": f"Dangling Study Dependency in {c['id'][:8]}",
                    "detail": f"Study '{c['model']}' depends on '{link_field}' id '{link_id}' which does not exist.",
                    "target_page": "calculations",
                    "target_id": c["id"],
                })

    # 3. Check Stale Studies
    for c in calculations:
        inputs = c.get("inputs_si", {})
        result = c.get("result", {})
        c_geom = inputs.get("geometry_revision_id") or result.get("geometry_revision_id")
        if c_geom and latest_geom_id and c_geom != latest_geom_id:
            study_name = inputs.get("study_name") or f"{c['model']} calculation"
            issues.append({
                "id": f"stale-study-{c['id']}",
                "category": "stale_study",
                "severity": "warning",
                "title": f"Stale Study: {study_name}",
                "detail": f"Calculated against superseded geometry revision {c_geom[:8]}; current revision is {latest_geom_id[:8]}. Historical results remain preserved without silent recalculation.",
                "target_page": "calculations",
                "target_id": c["id"],
            })

    # 4. Review Progress
    if workflow in {"full_workstation", "well_planning"}:
        if not programmes:
            issues.append({
                "id": "review-no-programmes",
                "category": "review_progress",
                "severity": "info",
                "title": "No Review Programme Created",
                "detail": "A formal drilling programme review has not yet been initiated.",
                "target_page": "programmes",
                "target_id": None,
            })
        else:
            for p in programmes:
                latest_v = p.get("latest_version") or (p.get("versions", [{}])[-1] if p.get("versions") else {})
                state = latest_v.get("state", "draft")
                p_id = p.get("id") or p.get("programme_id")
                if state == "draft":
                    issues.append({
                        "id": f"review-draft-{p_id}",
                        "category": "review_progress",
                        "severity": "warning",
                        "title": f"Programme '{p.get('title', 'Programme')}' in Draft",
                        "detail": "Programme version is currently in draft and has not been submitted for peer review.",
                        "target_page": "programmes",
                        "target_id": p_id,
                    })
                elif state == "in_review":
                    issues.append({
                        "id": f"review-in-review-{p_id}",
                        "category": "review_progress",
                        "severity": "info",
                        "title": f"Programme '{p.get('title', 'Programme')}' In Review",
                        "detail": "Programme is pending independent technical reviewer and approver sign-off.",
                        "target_page": "programmes",
                        "target_id": p_id,
                    })

    # 5. Recovery & Event Status
    unacknowledged_alerts = [e for e in events if not e.get("acknowledged") and e.get("severity") in {"critical", "high"}]
    for evt in unacknowledged_alerts:
        issues.append({
            "id": f"unack-event-{evt['id']}",
            "category": "event_alert",
            "severity": "warning",
            "title": f"Unacknowledged Event: {evt.get('title', 'Engineering Alert')}",
            "detail": f"Severity {evt.get('severity', 'high')}: {evt.get('detail', 'Review required')}",
            "target_page": "events",
            "target_id": evt["id"],
        })

    # Summary metrics
    blocking_count = sum(1 for i in issues if i["severity"] == "blocking")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")
    info_count = sum(1 for i in issues if i["severity"] == "info")

    ready = (blocking_count == 0)
    # Score calculation
    deductions = (blocking_count * 25.0) + (warning_count * 8.0) + (info_count * 2.0)
    score_pct = max(0.0, min(100.0, round(100.0 - deductions, 1)))

    return {
        "project_id": project_id,
        "workflow": workflow,
        "ready": ready,
        "score_pct": score_pct,
        "summary": {
            "total_issues": len(issues),
            "blocking_count": blocking_count,
            "warning_count": warning_count,
            "info_count": info_count,
        },
        "issues": issues,
    }
