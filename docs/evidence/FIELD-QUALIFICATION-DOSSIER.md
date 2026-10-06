# GeoDrill Pro — Provisional engineering benchmark dossier

Generated: 2026-10-06T08:13:04.863610+00:00

Qualification status: **INDEPENDENT_QUALIFICATION_PENDING**.
No independent reviewer, engineering board approval or commercial certification
has been supplied. The former automated field-qualification seal is withdrawn.

| Example | Numerical status | Provenance | Embedded-value SHA-256 |
|---|---|---|---|
| volve_directional_survey | numerical_check_passed | Unverified embedded example | 08f36ba5ddbdcf39ee7940fc110622b4f92bf1b246eb2e389f16921ec6cfcf80 |
| volve_hydraulics_ecd | numerical_check_passed | Unverified embedded example | 955d2a6d68ed4cee065d79aec59461e8044ac46584be4ffecd24e6baebe3a21e |
| utah_forge_dynamics | numerical_check_failed | Unverified embedded example | f9aea960bc9e522b198281ae26ec646dc5cb4058e5c8920099a229f5d4a80790 |
| tudrp_flowloop_cuttings | numerical_check_passed | Unverified embedded example | b65031f65495ec9756f4d45c3ac784529754bcd9cd27f86396bd06a2ce073c4f |
| downhole_sub_friction | withheld | Unverified embedded example | 2ae7095c8768905b14f8999abcf33848754bf679eadbce8e2b03aca0bf2f4df3 |

These hashes identify serialized values embedded in the code. They do not identify
an original Equinor, FORGE, Tulsa or service-company source document.
The flow-loop example fits embedded targets and does not test the production
transport model independently. The friction example is withheld because its
former arithmetic reconstructed its own observations. The FORGE example's
12.9/25.9 Hz axial modes do not intersect its claimed 14–18 Hz band; the complete
example therefore fails even though the torsional-frequency check agrees.

Evidence required to close the independent qualification gate:

- Original source files, license records and extraction locations with file SHA-256 digests
- Independent targets and declared applicability, tolerances and uncertainty
- Production-model execution and disjoint calibration/holdout observations
- Named independent engineering reviewer and signed scope-specific assessment

See SOURCE-PROVENANCE.md for source discovery and acquisition status.
The existing ISCWSA diagnostic comparison remains separate analytical verification.
Equipment control is false and automated drilling clearance is false.

Reproduce with python tools/generate_field_qualification_dossier.py.
The adjacent JSON retains all calculated values and failure reasons.
