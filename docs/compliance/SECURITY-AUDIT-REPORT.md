# Internal security verification record — 6 October 2026

The former Gate 4 closure, commercial deployment seal and COMPLIANT matrix are
withdrawn. This document records internal software checks. No external auditor,
SOC 2 report or ISO/IEC 27001 certificate has been supplied.

Current full regression: 568 passed, zero failures/errors, one Starlette/httpx
deprecation warning. Security cases cover named authentication, project isolation,
role restrictions, programme identity separation, signatures, tampered archives
and input rejection. This is test evidence within the implemented scope, not an
exhaustive penetration test.

Bandit: zero reported issues across services and packages, with six existing
suppressed checks. The scanner scope excludes frontend, build tooling and
organizational controls. Dependency audit: 93 applicable pinned dependencies,
zero known vulnerabilities and zero skipped dependencies at the recorded time.
Neither result guarantees the absence of undiscovered vulnerabilities.

Source-confirmed authentication uses per-user scrypt password hashing and random
opaque session tokens, with only token SHA-256 values stored. It does not issue JWTs.
Ed25519 attestations bind programme decision content; protected key custody and
independently established public-key trust remain part of deployment assurance.

The Windows research artifacts are explicitly unsigned. The publisher release
pipeline now refuses to label missing/untrusted signatures as a signed release.
Actual per-artifact state and hashes are recorded separately from security tests.

Reproduction commands and current results are in
[repair-verification.json](../evidence/repair-verification.json). External security
review, organizational compliance controls and certification remain pending.
Equipment control and automated drilling clearance remain unavailable.
