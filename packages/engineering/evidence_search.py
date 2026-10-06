"""Permission-aware evidence search with exact citations, revision hashes, and abstention (GD-A18).

Provides:
- Role-based project-scoped evidence search across datasets, geometries, studies, and programmes.
- Exact citations with file SHA-256 hash, revision ID, depth/station interval, and model version.
- Explicit conflicting-version detection and disclosure across historical revisions.
- Rigorous abstention when evidence is insufficient, contradictory, or unauthorized.
"""
from __future__ import annotations

import re
import hashlib
import json
from typing import Any, Dict, List, Literal, Optional, TypedDict
from pydantic import Field, model_validator

from .models import Contract


class SearchQuery(Contract):
    query: str = Field(min_length=1, max_length=500)
    project_id: str = Field(min_length=1, max_length=100)
    user_id: str = Field(min_length=1, max_length=100)
    user_role: Literal["viewer", "author", "reviewer", "approver", "admin", "unauthenticated"]
    target_domains: Optional[List[Literal["surveys", "geometry", "calculations", "programmes", "datasets", "qualification"]]] = None


class CitationRecord(TypedDict):
    domain: str
    entity_id: str
    title: str
    sha256_hash: str
    revision_id: Optional[str]
    interval_or_depth: Optional[str]
    matched_snippet: str
    model_version: Optional[str]
    created_at: Optional[str]


class ConflictingVersionRecord(TypedDict):
    parameter_name: str
    revisions: List[Dict[str, Any]]
    conflict_summary: str


class SearchResult(TypedDict):
    query: str
    project_id: str
    authorized: bool
    authorization_error: Optional[str]
    abstention: bool
    abstention_reason: Optional[str]
    conflicting_versions: List[ConflictingVersionRecord]
    citations: List[CitationRecord]
    answer_summary: Optional[str]


def search_project_evidence(
    query_input: SearchQuery,
    project: Dict[str, Any],
    datasets: List[Dict[str, Any]],
    geometry_revisions: List[Dict[str, Any]],
    calculations: List[Dict[str, Any]],
    programmes: List[Dict[str, Any]],
    user_project_memberships: Optional[List[str]] = None,
) -> SearchResult:
    """Execute permission-aware search with exact citations and conflict disclosure."""
    qid = query_input.project_id
    role = query_input.user_role

    # 1. Authorization check
    if role == "unauthenticated":
        return {
            "query": query_input.query,
            "project_id": qid,
            "authorized": False,
            "authorization_error": "Authentication required. Unauthenticated requests are blocked.",
            "abstention": True,
            "abstention_reason": "Access denied: unauthenticated.",
            "conflicting_versions": [],
            "citations": [],
            "answer_summary": None,
        }

    if user_project_memberships is not None and qid not in user_project_memberships:
        return {
            "query": query_input.query,
            "project_id": qid,
            "authorized": False,
            "authorization_error": f"User '{query_input.user_id}' does not have membership in project '{qid}'.",
            "abstention": True,
            "abstention_reason": "Access denied: insufficient project membership.",
            "conflicting_versions": [],
            "citations": [],
            "answer_summary": None,
        }

    q_terms = [t.lower() for t in query_input.query.strip().split() if len(t) > 2]
    if not q_terms:
        q_terms = [query_input.query.strip().lower()]

    domains = query_input.target_domains or ["surveys", "geometry", "calculations", "programmes", "datasets", "qualification"]
    citations: List[CitationRecord] = []

    # 2. Search Datasets
    if "datasets" in domains or "surveys" in domains:
        for ds in datasets:
            match = False
            haystack = f"{ds.get('filename', '')} {ds.get('kind', '')} {ds.get('id', '')}".lower()
            if any(term in haystack for term in q_terms):
                match = True
            if match:
                citations.append({
                    "domain": "datasets",
                    "entity_id": ds.get("id", ""),
                    "title": ds.get("filename", "Dataset"),
                    "sha256_hash": ds.get("source_hash", ds.get("sha256", "unknown")),
                    "revision_id": None,
                    "interval_or_depth": f"0 to {ds.get('row_count', 'unknown')} rows",
                    "matched_snippet": f"Dataset {ds.get('kind', '')} '{ds.get('filename')}' ({ds.get('row_count', 0)} rows)",
                    "model_version": None,
                    "created_at": ds.get("created_at"),
                })

    # 3. Search Geometry Revisions
    if "geometry" in domains:
        for rev in geometry_revisions:
            haystack = f"{rev.get('change_note', '')} {rev.get('id', '')} {rev.get('sha256', '')}".lower()
            casings_text = " ".join(c.get("name", "") for c in rev.get("input", {}).get("casings", []))
            haystack += " " + casings_text.lower()
            if any(term in haystack for term in q_terms):
                citations.append({
                    "domain": "geometry",
                    "entity_id": rev.get("id", ""),
                    "title": f"Geometry Revision ({rev.get('id', '')[:8]})",
                    "sha256_hash": rev.get("sha256", "unknown"),
                    "revision_id": rev.get("id"),
                    "interval_or_depth": f"Casings: {len(rev.get('input', {}).get('casings', []))}",
                    "matched_snippet": f"Change note: {rev.get('change_note', 'Standard revision')}",
                    "model_version": "M01-geometry",
                    "created_at": rev.get("created_at"),
                })

    # 4. Search Calculations
    if "calculations" in domains:
        for calc in calculations:
            model = calc.get("model", "")
            inputs = calc.get("inputs_si", {})
            result = calc.get("result", {})
            study_name = inputs.get("study_name", f"{model} study")
            haystack = f"{model} {study_name} {calc.get('id', '')}".lower()
            if any(term in haystack for term in q_terms):
                citations.append({
                    "domain": "calculations",
                    "entity_id": calc.get("id", ""),
                    "title": study_name,
                    "sha256_hash": hashlib.sha256(json.dumps(calc, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
                    "revision_id": inputs.get("geometry_revision_id"),
                    "interval_or_depth": f"Geometry revision: {inputs.get('geometry_revision_id', 'not supplied')}",
                    "matched_snippet": f"Model '{model}' study with status '{result.get('status', 'complete')}'",
                    "model_version": result.get("model_version", "1.0.0"),
                    "created_at": calc.get("created_at"),
                })

    # 5. Search Programmes
    if "programmes" in domains:
        for prog in programmes:
            title = prog.get("title", "Programme")
            for version in prog.get("versions", [prog]):
                state = version.get("state", prog.get("status", "unknown"))
                haystack = f"{title} {state} {prog.get('id', '')} {version.get('id', '')}".lower()
                if not any(term in haystack for term in q_terms):
                    continue
                citations.append({
                    "domain": "programmes",
                    "entity_id": prog.get("id", ""),
                    "title": title,
                    "sha256_hash": version.get("content_sha256", prog.get("sha256", "unknown")),
                    "revision_id": version.get("id") if "versions" in prog else prog.get("revision_id"),
                    "interval_or_depth": f"Evidence bindings: {len(version.get('evidence_bindings', []))}",
                    "matched_snippet": f"Programme '{title}' version {version.get('version_no', 'unknown')} in status '{state}'",
                    "model_version": None,
                    "created_at": version.get("created_at", prog.get("created_at")),
                })

    # 6. Check for Conflicting Versions across Geometries
    conflicts: List[ConflictingVersionRecord] = []
    # Historical changes are disclosed only for matching geometry queries. They
    # do not manufacture a result for an unrelated question with zero citations.
    if "geometry" in domains and any(c["domain"] == "geometry" for c in citations):
        histories: Dict[str, List[Dict[str, Any]]] = {}
        for rev in geometry_revisions:
            for casing in rev.get("input", {}).get("casings", []):
                histories.setdefault(casing.get("name", "Unnamed casing"), []).append({
                    "revision_id": rev.get("id"), "sha256": rev.get("sha256"),
                    "shoe_md_m": casing.get("bottom_md_m"), "id_m": casing.get("inside_diameter_m"),
                    "change_note": rev.get("change_note"),
                })
        for cname, history in histories.items():
            if len({(r["shoe_md_m"], r["id_m"]) for r in history}) > 1:
                conflicts.append({
                    "parameter_name": f"Casing '{cname}' Shoe Depth / ID", "revisions": history,
                    "conflict_summary": f"Casing '{cname}' has different shoe depths or inside diameters across {len(history)} historical revisions. Select the intended immutable revision before interpreting a study.",
                })

    # 7. Abstention Evaluation
    if not citations:
        return {
            "query": query_input.query,
            "project_id": qid,
            "authorized": True,
            "authorization_error": None,
            "abstention": True,
            "abstention_reason": f"No verified evidence found matching '{query_input.query}' in project '{qid}'. Abstaining from answering.",
            "conflicting_versions": [],
            "citations": [],
            "answer_summary": None,
        }

    # Generate grounded summary
    summary_parts = [f"Found {len(citations)} exact citations across {len(set(c['domain'] for c in citations))} domains."]
    if conflicts:
        summary_parts.append(f"Caution: {len(conflicts)} conflicting version(s) identified in historical project revisions.")

    return {
        "query": query_input.query,
        "project_id": qid,
        "authorized": True,
        "authorization_error": None,
        "abstention": bool(conflicts),
        "abstention_reason": "Historical geometry values differ. Citations are retained, but a single current engineering answer is withheld until the intended revision is selected." if conflicts else None,
        "conflicting_versions": conflicts,
        "citations": citations,
        "answer_summary": " ".join(summary_parts),
    }
