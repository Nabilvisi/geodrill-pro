"""Tests for permission-aware evidence search (GD-A18)."""
from __future__ import annotations

import pytest
from packages.engineering.evidence_search import (
    SearchQuery,
    search_project_evidence,
)


def test_evidence_search_unauthenticated_blocked():
    query = SearchQuery(
        query="casing depth",
        project_id="proj-alpha",
        user_id="anonymous",
        user_role="unauthenticated",
    )
    res = search_project_evidence(
        query_input=query,
        project={"id": "proj-alpha", "name": "Alpha Well"},
        datasets=[],
        geometry_revisions=[],
        calculations=[],
        programmes=[],
        user_project_memberships=["proj-alpha"],
    )
    assert res["authorized"] is False
    assert res["abstention"] is True
    assert "Authentication required" in (res["authorization_error"] or "")
    assert len(res["citations"]) == 0


def test_evidence_search_project_membership_denied():
    query = SearchQuery(
        query="casing shoe",
        project_id="proj-secret",
        user_id="user-123",
        user_role="viewer",
    )
    res = search_project_evidence(
        query_input=query,
        project={"id": "proj-secret", "name": "Secret Well"},
        datasets=[],
        geometry_revisions=[],
        calculations=[],
        programmes=[],
        user_project_memberships=["proj-public"],  # Not a member of proj-secret
    )
    assert res["authorized"] is False
    assert res["abstention"] is True
    assert "membership" in (res["authorization_error"] or "")
    assert len(res["citations"]) == 0


def test_evidence_search_exact_citations_and_hashes():
    query = SearchQuery(
        query="casing survey",
        project_id="proj-alpha",
        user_id="engineer-1",
        user_role="author",
    )
    datasets = [
        {
            "id": "ds-surv-1",
            "filename": "directional_survey.csv",
            "kind": "survey",
            "source_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
            "row_count": 45,
            "created_at": "2026-03-01T10:00:00Z",
        }
    ]
    geometries = [
        {
            "id": "geom-rev-1",
            "sha256": "f0e1d2c3b4a5968778695a4b3c2d1e0f0123456789abcdef0123456789abcdef",
            "change_note": "Initial 9-5/8 casing design",
            "input": {
                "casings": [
                    {"name": "9-5/8 Surface Casing", "bottom_md_m": 1200.0, "inside_diameter_m": 0.224}
                ]
            },
            "created_at": "2026-03-01T11:00:00Z",
        }
    ]
    calculations = [
        {
            "id": "calc-hyd-1",
            "model": "M03-hydraulics",
            "inputs_si": {"study_name": "Hydraulics Casing Run", "geometry_revision_id": "geom-rev-1"},
            "result": {
                "status": "complete",
                "model_version": "2.1.0",
                "geometry_sha256": "f0e1d2c3b4a5968778695a4b3c2d1e0f0123456789abcdef0123456789abcdef",
                "total_depth_md_m": 1200.0,
            },
            "created_at": "2026-03-01T12:00:00Z",
        }
    ]
    programmes = [
        {
            "id": "prog-1",
            "title": "Casing & Cementing Programme",
            "status": "approved",
            "sha256": "0987654321fedcba0987654321fedcba0987654321fedcba0987654321fedcba",
            "revision_id": "prog-rev-1",
            "bound_study_ids": ["calc-hyd-1"],
            "attestations": ["sig1", "sig2"],
            "created_at": "2026-03-01T14:00:00Z",
        }
    ]

    res = search_project_evidence(
        query_input=query,
        project={"id": "proj-alpha"},
        datasets=datasets,
        geometry_revisions=geometries,
        calculations=calculations,
        programmes=programmes,
        user_project_memberships=["proj-alpha"],
    )

    assert res["authorized"] is True
    assert res["abstention"] is False
    assert len(res["citations"]) >= 3
    # Check that exact hashes are present
    hashes = [c["sha256_hash"] for c in res["citations"]]
    assert "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0" in hashes
    assert "f0e1d2c3b4a5968778695a4b3c2d1e0f0123456789abcdef0123456789abcdef" in hashes


def test_evidence_search_conflicting_versions_disclosure():
    query = SearchQuery(
        query="casing shoe depth",
        project_id="proj-alpha",
        user_id="engineer-1",
        user_role="author",
    )
    geometries = [
        {
            "id": "geom-rev-1",
            "sha256": "1111111111111111111111111111111111111111111111111111111111111111",
            "change_note": "First casing revision",
            "input": {
                "casings": [
                    {"name": "Production Casing", "bottom_md_m": 2500.0, "inside_diameter_m": 0.1778}
                ]
            },
        },
        {
            "id": "geom-rev-2",
            "sha256": "2222222222222222222222222222222222222222222222222222222222222222",
            "change_note": "Deepened shoe to avoid unstable shale",
            "input": {
                "casings": [
                    {"name": "Production Casing", "bottom_md_m": 2850.0, "inside_diameter_m": 0.1778}
                ]
            },
        },
    ]

    res = search_project_evidence(
        query_input=query,
        project={"id": "proj-alpha"},
        datasets=[],
        geometry_revisions=geometries,
        calculations=[],
        programmes=[],
        user_project_memberships=["proj-alpha"],
    )

    assert res["authorized"] is True
    assert len(res["conflicting_versions"]) == 1
    conflict = res["conflicting_versions"][0]
    assert "Production Casing" in conflict["parameter_name"]
    assert len(conflict["revisions"]) == 2
    assert conflict["revisions"][0]["shoe_md_m"] == 2500.0
    assert conflict["revisions"][1]["shoe_md_m"] == 2850.0
    assert "Caution: 1 conflicting version" in (res["answer_summary"] or "")


def test_evidence_search_strict_abstention_on_missing_evidence():
    query = SearchQuery(
        query="unobtainium nuclear drilling bit",
        project_id="proj-alpha",
        user_id="engineer-1",
        user_role="author",
    )
    res = search_project_evidence(
        query_input=query,
        project={"id": "proj-alpha"},
        datasets=[],
        geometry_revisions=[],
        calculations=[],
        programmes=[],
        user_project_memberships=["proj-alpha"],
    )

    assert res["authorized"] is True
    assert res["abstention"] is True
    assert "No verified evidence found" in (res["abstention_reason"] or "")
    assert len(res["citations"]) == 0
    assert res["answer_summary"] is None


def test_evidence_search_api_endpoint(tmp_path):
    from fastapi.testclient import TestClient
    from services.api.main import create_app

    app = create_app(data_dir=tmp_path)
    client = TestClient(app)
    client.headers["X-Geodrill-Client"] = "workstation"
    sess_res = client.get("/api/session")
    assert sess_res.status_code == 200

    proj = client.post("/api/projects", json={
        "name": "Alpha Well Project",
        "well_name": "AW-01",
        "datum": "Kelly Bushing RKB",
        "bit_diameter_m": 0.2159,
        "origin": "synthetic",
    }).json()
    proj_id = proj["id"]

    res = client.get(f"/api/projects/{proj_id}/evidence/search?q=casing")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == proj_id
    assert "authorized" in data
    assert "citations" in data
    assert "abstention" in data

