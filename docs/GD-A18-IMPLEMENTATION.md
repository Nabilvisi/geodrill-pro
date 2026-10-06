# GD-A18 — connected project evidence search

Evidence search is available in workstation navigation. It searches preserved
filenames/kinds, study names/models, record identifiers, geometry change notes and
casing names, and programme titles/version states. This is deterministic metadata
retrieval. Full document text retrieval and engineering question answering remain
unfinished scope.

GET /api/projects/{project_id}/evidence/search?q=... bounds queries to 500 characters
and follows the existing project membership boundary. Results expose exact record
and revision IDs with distinct hash bases: original imported-file bytes, immutable
geometry revisions, complete canonical saved calculations, and actual programme
version content. Calculation citations previously mislabeled geometry hashes;
this is corrected. Programme citations now retain every stored version, actual
content hashes and lifecycle state. No missing programme fetch is silently treated
as an empty successful search.

Inspect cited record reads the preserved project dataset, geometry, calculation
or programme. Large arrays preview 12 entries with an explicit retained count;
complete records remain in the workspace and fixed reports. The JSON view does
not claim to be original imported-file bytes.

Matching historical casing shoe/inside-diameter changes are disclosed across all
available geometry revisions. A single answer is withheld when those values vary.
An unrelated query with no citations abstains even if historical geometry changed.
Changes are versioned observations, not an automatic choice of current authority.
Conflict detection is limited to these casing parameters; it is not comprehensive
engineering contradiction detection.

Tests cover full-calculation hashing, actual programme-version citations, query
limits, no-match abstention, changes beyond the latest pair, project/role boundaries
and cited programme inspection. The UI clears prior results when queries change
and ignores responses superseded by a later query or project change.

Remaining acceptance: representative operator questions, broader evidence domains,
full-document retrieval, depth/station-specific citations where meaningful, wider
conflict detection and independent assessment. Search matches do not independently
qualify models or issue drilling clearance or equipment commands.
