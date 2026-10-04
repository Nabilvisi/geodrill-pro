# Implementation sequence and release gates

Baseline: GeoDrill Pro 0.8.0. Research date: 4 October 2026, Asia/Jakarta. This is a proposed implementation plan; no backlog work was implemented by this research.

## Tranche 1: connect current engineering work

Build A05 qualification cards alongside A01 source mapping/readiness, followed by A02 scenario/dependency bundles. Add A04 searchable records and unit presentation as the workflow takes shape, then A03 programme/review pack.

Deliverable: one end-to-end project, baseline plus two alternatives, preserved sources, stale-result tracking and a complete review package. Include valid, unknown and explicitly unsupported cases. Use the existing M6→M8/M9 and M10→M11 bindings rather than silently copying inputs.

Acceptance: an independent reviewer can reproduce eligible calculations and withholding from the package; every claimed source/model/revision resolves; old snapshots remain unchanged after revision; no stale assessment labelled current; complete records retained in linked annexes. Browser checks must exercise import, comparison, revision, export, reopen and readability with actual large records.

Measure baseline task time and errors before development. Proposed usability pilot: five representative users, the same anonymized tasks, no assistance beyond normal documentation. Compare completion, error recovery and source verification against baseline. A provisional target of at least 20% median task-time improvement and no new critical interpretation error is a product hypothesis; revise it with pilot design and report sample limitations. It is not promised performance.

## Tranche 2: connect daily delivery and adoption

A06 adds activities, DDR, NPT and cost reconciliation using explicitly agreed taxonomy/currency/time rules. A07 adds isolated read-only WITSML/ETP with selected objects and legacy mappings only when needed. A08 supplies consistent backup/restore and packaging. Introduce A09 named permissions and revision attestations before a shared/network deployment.

Acceptance: a reporting day reconciles including explicit gaps; totals and XML round-trip; reconnect/duplicates do not silently lose or invent records; clean-machine restore preserves hashes; conflicting edits cannot overwrite; reviewers attest exact content. Freeze and test supported adapter schemas and source authorization. Retain equipment_control false.

## Tranche 3: broaden core engineering with evidence

Run A10 positioning, A11 hydraulics/transport and A12 mechanics/transients as separately owned model workstreams. They are not interchangeable tests. A10 needs geodesy and pinned covariance references; A11 needs characterized fluids and measured pressure/solids cases; A12 needs loads with operational state and bias evidence. A13 follows a reviewed integrity/casing scope and local company/jurisdiction references.

Acceptance: predeclared numerical tolerances, analytical limits, conservation/refinement and independent benchmark agreement; experimental residuals and uncertainty by intended regime; unknown/outside-envelope inputs continue to withhold. Obtain specialist review before changing intended-use wording. A casing load result does not close barrier-test evidence.

## Tranche 4: specialist qualification and learning

A14 depends on useful daily records and comparable offsets. A15 needs calibrated BHA and inspected material/bit evidence. A16 needs independent field-event adjudication and passive evaluation authorization. A17 needs actual-fluid and formation characterization. A18 evidence search follows permissions, source dictionaries and revision handling.

Acceptance: disjoint training/validation cases, preserved availability time, clear uncertainty and exclusions; measured performance only within evaluated populations. Evidence search must cite exact file/page and abstain when the record cannot support an answer.

## Sequencing choices requiring interviews

If DDR preparation is the strongest repeated pain, bring A06 forward immediately after A01/A02. If a directional contractor supplies usable error models and reference offsets, bring A10 forward after A05. If the initial buyer requires offline deployment, make A08 a first-tranche gate. These are choices for the interview/pilot evidence, not assumptions already settled.

## Scope and authority

A19 is excluded. Do not add hardware writes, rig authorization, automatic operator clearance, OEM adapters or equipment leases. Module 17 remains isolated simulation. Do not purchase, contact people or acquire commercial licences as a consequence of this plan without separate authorization.

Effort S/M/L/XL is relative sizing only. Calendar estimates require owners, data access, model scope and acceptance tolerances. A numerical check, usable demo and field qualification are separate release states.
