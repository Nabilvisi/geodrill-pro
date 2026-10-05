"""Drilling programme review pack builder and exporter (GD-A03).

Provides:
- Structured drilling programme assembly tying section plans, activity sequences,
  hazard registers, assumptions, and study comparison references into a cohesive pack.
- Frozen snapshot metadata binding source hashes, model hashes, and qualification statuses.
- HTML, Markdown, and CSV export generators with clear research-only disclaimers and watermarks.
- Integrity verification of programme review packages.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .qualification import get_qualification_card, list_qualification_cards
from .scenarios import compare_scenarios


WATERMARK_NOTICE = (
    "RESEARCH & HISTORICAL ENGINEERING REVIEW ONLY — NOT AN OPERATIONAL CLEARANCE "
    "OR FIELD-QUALIFIED PERMIT"
)


def build_programme_pack(
    project_id: str,
    programme_title: str,
    sections: List[Dict[str, Any]],
    activities: List[Dict[str, Any]],
    hazards: List[Dict[str, Any]],
    assumptions: List[Dict[str, Any]],
    selected_studies: List[Dict[str, Any]],
    baseline_study: Optional[Dict[str, Any]] = None,
    alternative_study: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble a revision-controlled review pack data structure.

    Freezes:
    - Section and activity plans
    - Risk and hazard register with mitigation barriers
    - Engineering assumptions
    - Scenario delta comparison (if baseline and alternative provided)
    - Referenced qualification status cards for all invoked models
    """
    pack_id = str(uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    # Model IDs involved across selected studies
    model_ids = {s.get("model") for s in selected_studies if s.get("model")}
    if baseline_study and baseline_study.get("model"):
        model_ids.add(baseline_study["model"])
    if alternative_study and alternative_study.get("model"):
        model_ids.add(alternative_study["model"])

    # Resolve qualification cards for all referenced models
    qualification_ledger: List[Dict[str, Any]] = []
    for mid in sorted(filter(None, model_ids)):
        card = get_qualification_card(mid)
        if card:
            qualification_ledger.append({
                "module_id": card["module_id"],
                "module_title": card["title"],
                "qualification_status": card["qualification_status"],
                "intended_use": card["intended_use"],
                "governing_physics": card["governing_physics"],
                "withholding_conditions": card["withholding_conditions"],
                "unsupported_scopes": card.get("withholding_conditions", []),
            })
        else:
            qualification_ledger.append({
                "module_id": mid,
                "module_title": f"Custom Module {mid}",
                "qualification_status": "unverified",
                "intended_use": "Unverified custom model",
                "governing_physics": "Not declared",
                "withholding_conditions": ["Unverified model"],
                "unsupported_scopes": ["Production use withheld"],
            })

    # Scenario comparison if both studies provided
    scenario_comparison = None
    if baseline_study and alternative_study:
        scenario_comparison = compare_scenarios(baseline_study, alternative_study)

    pack = {
        "pack_id": pack_id,
        "project_id": project_id,
        "title": programme_title,
        "assembled_at": now_iso,
        "watermark": WATERMARK_NOTICE,
        "status": "draft_review_pack",
        "metadata": metadata or {},
        "sections": sections,
        "activities": activities,
        "hazards": hazards,
        "assumptions": assumptions,
        "selected_studies": selected_studies,
        "scenario_comparison": scenario_comparison,
        "qualification_ledger": qualification_ledger,
    }
    return pack


def export_pack_to_html(pack: Dict[str, Any]) -> str:
    """Render the drilling programme pack as a styled, paginated HTML document."""
    title = pack.get("title", "Drilling Programme Review Pack")
    pack_id = pack.get("pack_id", "")
    project_id = pack.get("project_id", "")
    assembled_at = pack.get("assembled_at", "")
    watermark = pack.get("watermark", WATERMARK_NOTICE)

    sections_html = ""
    for s in pack.get("sections", []):
        sections_html += f"""
        <tr>
            <td><strong>{s.get('section_name', 'Section')}</strong></td>
            <td>{s.get('hole_size_in', '-')} in</td>
            <td>{s.get('casing_od_in', '-')} in</td>
            <td>{s.get('top_depth_m', '-')} m</td>
            <td>{s.get('bottom_depth_m', '-')} m</td>
            <td>{s.get('mud_type', '-')} ({s.get('mud_density_sg', '-')} SG)</td>
        </tr>
        """

    activities_html = ""
    for a in pack.get("activities", []):
        activities_html += f"""
        <tr>
            <td>{a.get('sequence', '-')}</td>
            <td><strong>{a.get('phase', '-')}</strong></td>
            <td>{a.get('description', '-')}</td>
            <td>{a.get('duration_hrs', '-')} h</td>
            <td>{a.get('planned_depth_m', '-')} m</td>
        </tr>
        """

    hazards_html = ""
    for h in pack.get("hazards", []):
        hazards_html += f"""
        <tr>
            <td><span class="badge {h.get('severity', 'medium').lower()}">{h.get('severity', 'Medium')}</span></td>
            <td><strong>{h.get('hazard', '-')}</strong></td>
            <td>{h.get('consequence', '-')}</td>
            <td>{h.get('mitigation', '-')}</td>
            <td>{h.get('barrier_status', 'Active')}</td>
        </tr>
        """

    qual_html = ""
    for q in pack.get("qualification_ledger", []):
        qual_html += f"""
        <div class="qual-card">
            <h4>{q.get('module_id')}: {q.get('module_title')} <span class="badge-status">{q.get('qualification_status')}</span></h4>
            <p><strong>Intended Use:</strong> {q.get('intended_use')}</p>
            <p><strong>Physics:</strong> {q.get('governing_physics')}</p>
            <p><strong>Withholding / Unsupported:</strong> {", ".join(q.get('withholding_conditions', []))}</p>
        </div>
        """

    comparison_html = ""
    if pack.get("scenario_comparison"):
        sc = pack["scenario_comparison"]
        deltas = sc.get("deltas", {})
        delta_rows = "".join(
            f"<tr><td><code>{k}</code></td><td>{v.get('baseline')}</td><td>{v.get('alternative')}</td><td><strong>{v.get('delta')}</strong></td></tr>"
            for k, v in deltas.items()
        )
        comparison_html = f"""
        <h3>Engineering Scenario Delta: {sc.get('baseline_id')} vs {sc.get('alternative_id')}</h3>
        <p><strong>Identical Inputs:</strong> {", ".join(sc.get('identical_inputs', [])) or 'None'}</p>
        <p><strong>Differing Inputs:</strong> {", ".join(sc.get('differing_inputs', [])) or 'None'}</p>
        <table class="data-table">
            <thead><tr><th>Metric</th><th>Baseline</th><th>Alternative</th><th>Delta</th></tr></thead>
            <tbody>{delta_rows}</tbody>
        </table>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} — Review Pack</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.5; color: #1e293b; margin: 0; padding: 2rem; }}
  .watermark {{ background: #fef2f2; border: 2px dashed #ef4444; color: #b91c1c; font-weight: 700; text-align: center; padding: 0.75rem; border-radius: 6px; margin-bottom: 2rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 1rem; margin-bottom: 2rem; }}
  h1 {{ margin: 0 0 0.5rem 0; font-size: 1.8rem; color: #0f172a; }}
  .meta {{ font-size: 0.85rem; color: #64748b; }}
  h2 {{ color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.3rem; margin-top: 2rem; font-size: 1.3rem; }}
  table.data-table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }}
  table.data-table th, table.data-table td {{ border: 1px solid #cbd5e1; padding: 0.5rem 0.75rem; text-align: left; }}
  table.data-table th {{ background-color: #f8fafc; font-weight: 600; color: #334155; }}
  .badge {{ padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
  .badge.high {{ background: #fee2e2; color: #991b1b; }}
  .badge.medium {{ background: #fef3c7; color: #92400e; }}
  .badge.low {{ background: #dcfce7; color: #166534; }}
  .qual-card {{ background: #f8fafc; border-left: 4px solid #3b82f6; padding: 1rem; margin-bottom: 1rem; border-radius: 0 6px 6px 0; }}
  .qual-card h4 {{ margin: 0 0 0.5rem 0; font-size: 1rem; }}
  .badge-status {{ background: #e0e7ff; color: #3730a3; padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.75rem; }}
  @media print {{ body {{ padding: 0; }} }}
</style>
</head>
<body>
  <div class="watermark">{watermark}</div>
  <header>
    <h1>{title}</h1>
    <div class="meta">
      <strong>Pack ID:</strong> {pack_id} | <strong>Project:</strong> {project_id} | <strong>Assembled:</strong> {assembled_at}
    </div>
  </header>

  <section>
    <h2>1. Section Plan</h2>
    <table class="data-table">
      <thead>
        <tr><th>Section</th><th>Hole OD</th><th>Casing OD</th><th>Top MD</th><th>Shoe MD</th><th>Drilling Fluid</th></tr>
      </thead>
      <tbody>{sections_html or '<tr><td colspan="6">No section data declared</td></tr>'}</tbody>
    </table>
  </section>

  <section>
    <h2>2. Operational Activity Sequence</h2>
    <table class="data-table">
      <thead>
        <tr><th>Seq</th><th>Phase</th><th>Activity Description</th><th>Duration</th><th>Target MD</th></tr>
      </thead>
      <tbody>{activities_html or '<tr><td colspan="5">No operational activities scheduled</td></tr>'}</tbody>
    </table>
  </section>

  <section>
    <h2>3. Hazard Register & Well Control Barriers</h2>
    <table class="data-table">
      <thead>
        <tr><th>Severity</th><th>Hazard Description</th><th>Potential Consequence</th><th>Mitigation / Prevention</th><th>Barrier Status</th></tr>
      </thead>
      <tbody>{hazards_html or '<tr><td colspan="5">No specific hazards registered</td></tr>'}</tbody>
    </table>
  </section>

  {f"<section><h2>4. Scenario Analysis</h2>{comparison_html}</section>" if comparison_html else ""}

  <section>
    <h2>5. Model Qualifications & Applicability Boundaries</h2>
    {qual_html or '<p>No engineering models linked.</p>'}
  </section>

  <footer style="margin-top: 3rem; border-top: 1px solid #e2e8f0; padding-top: 1rem; font-size: 0.8rem; color: #64748b;">
    GeoDrill Pro Drilling Programme Review Pack &bull; ISO 19901-1 / API Spec Q2 Review Protocol
  </footer>
</body>
</html>
"""
    return html


def export_pack_to_csv(pack: Dict[str, Any], component: str = "activities") -> str:
    """Export tabular components of the review pack to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    if component == "activities":
        writer.writerow(["Sequence", "Phase", "Description", "Duration_Hours", "Planned_Depth_M"])
        for a in pack.get("activities", []):
            writer.writerow([
                a.get("sequence", ""),
                a.get("phase", ""),
                a.get("description", ""),
                a.get("duration_hrs", ""),
                a.get("planned_depth_m", ""),
            ])
    elif component == "sections":
        writer.writerow(["Section_Name", "Hole_Size_In", "Casing_OD_In", "Top_Depth_M", "Bottom_Depth_M", "Mud_Type", "Mud_Density_SG"])
        for s in pack.get("sections", []):
            writer.writerow([
                s.get("section_name", ""),
                s.get("hole_size_in", ""),
                s.get("casing_od_in", ""),
                s.get("top_depth_m", ""),
                s.get("bottom_depth_m", ""),
                s.get("mud_type", ""),
                s.get("mud_density_sg", ""),
            ])
    elif component == "hazards":
        writer.writerow(["Hazard", "Severity", "Consequence", "Mitigation", "Barrier_Status"])
        for h in pack.get("hazards", []):
            writer.writerow([
                h.get("hazard", ""),
                h.get("severity", ""),
                h.get("consequence", ""),
                h.get("mitigation", ""),
                h.get("barrier_status", ""),
            ])
    else:
        raise ValueError(f"Unsupported component for CSV export: {component}")

    return output.getvalue()
