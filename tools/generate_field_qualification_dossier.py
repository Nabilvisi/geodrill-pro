"""Generate a provisional benchmark dossier without inventing approval or reviewers."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.engineering.field_qualification import run_all_field_qualifications


def generate_dossier(output_dir: Path | None = None) -> Path:
    results = run_all_field_qualifications()
    out_dir = output_dir or ROOT / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "FIELD-QUALIFICATION-DOSSIER.md"
    rows = []
    for key, value in results["benchmarks"].items():
        status = value.get("status", "numerical_check_passed" if value["passed"] else "numerical_check_failed")
        rows.append(f"| {key} | {status} | {value['validation_status']} | Unverified embedded example | {value['data_sha256']} |")
    missing = "\n".join(f"- {item}" for item in results["missing_evidence"])
    text = f"""# GeoDrill Pro — Provisional engineering benchmark dossier

Generated: {datetime.now(timezone.utc).isoformat()}

Qualification status: **{results['overall_status']}**.
No independent reviewer, engineering board approval or commercial certification
has been supplied. The former automated field-qualification seal is withdrawn.

| Example | Numerical status | Independent validation | Provenance | Embedded-value SHA-256 |
|---|---|---|---|---|
{chr(10).join(rows)}

These hashes identify serialized values embedded in the code. They do not identify
an original Equinor, FORGE, Tulsa or service-company source document.
Direct calls to each example also withhold independent validation and do not assign
a source license. The survey comparison checks the horizontal coordinate vector;
matching radial displacement alone cannot pass a reflected trajectory.
The flow-loop example fits embedded targets and does not test the production
transport model independently. The friction example is withheld because its
former arithmetic reconstructed its own observations. The FORGE example's
12.9/25.9 Hz axial modes do not intersect its claimed 14–18 Hz band; the complete
example therefore fails even though the torsional-frequency check agrees.

Evidence required to close the independent qualification gate:

{missing}

See SOURCE-PROVENANCE.md for source discovery and acquisition status.
The existing ISCWSA diagnostic comparison remains separate analytical verification.
Equipment control is false and automated drilling clearance is false.

Reproduce with python tools/generate_field_qualification_dossier.py.
The adjacent JSON retains all calculated values and failure reasons.
"""
    out_path.write_text(text, encoding="utf-8")
    (out_dir / "field-qualification-results.json").write_text(
        json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return out_path


if __name__ == "__main__":
    print(generate_dossier())
