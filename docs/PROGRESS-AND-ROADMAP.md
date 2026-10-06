# GeoDrill Pro — progress and remaining roadmap

7 October 2026 v0.9 reconciliation: the current source is **0.9.0-alpha.1**. Use [the v0.9 architecture audit](V09-ARCHITECTURE-AUDIT.md), [progress record](../GEODRILL_PRO_V0.9_PROGRESS.md) and [verification evidence](evidence/v09-verification.json) for current distribution and acceptance status. The all-phases-complete claim is withdrawn. The roadmap below retains the earlier GD-A increments and their dated release evidence; those milestones do not establish completion of the v0.9 architecture.

Updated 6 October 2026. This file supersedes the former 485/537-test progress
snapshots and blanket "advancement complete" declaration. Historical command
records remain in [VERIFICATION.md](VERIFICATION.md).

PR 1 is merged. The hosted app and unsigned research-5 Windows packages
are published and verified at source 77e3e91885b9994f6ed0eedee85bb7567e6738f6,
with 635 passing tests locally, on Windows/Ubuntu CI and in the Windows release job. See
[current publication evidence](evidence/geomechanics-verification.json) and
[repair status](REPAIR-STATUS.md).

The completion audit found additional software gaps. Read
[the current delivery matrix](IMPROVEMENT-PLAN.md) for every increment and its
remaining acceptance criteria. Current recovery work adds whole-workstation
snapshot/restore, atomic failed migrations, preserved project-study reopening and
archive/identity validation. Research-4 also includes connected offset benchmarking
and evidence search; research-5 adds connected survey-bound formation geomechanics. Historical release evidence remains separately recorded.

Remaining implementation sequence:

1. Expand recovery acceptance to broader interrupted-write/disk-full cases and
   clean-machine operator checks. Packaged backup/restore passed in research-4;
   automatic update/binary rollback remains a separate unfinished feature.
2. Build the isolated read-only ETP/WITSML adapter with original/receipt/source time,
   ordering, duplicates, reconnect, quarantine and declared supported-object fixtures.
3. Offset benchmarking and evidence search now have connected UI/import/citation
   workflows with deployment/package verification complete in research-4. Complete
   representative operator acceptance. Formation geomechanics now has a repaired
   survey-bound workflow; actual-fluid/coupled solver scope remains unfinished,
   together with dedicated team and directional integration.
4. Expand hydraulics/contact/transient closures only with declared applicability,
   measured prerequisites and independent reference/holdout comparisons. Restricted
   mixture-density and bending-gradient implementations do not close these items.
5. Complete trusted publisher signing, original-source engineering qualification
   and external security/compliance review with actual owner/reviewer evidence.

The original [backlog](research/post-module-17/BACKLOG.md) and
[implementation sequence](research/post-module-17/IMPLEMENTATION-SEQUENCE.md) retain
their acceptance criteria. Full completion is not declared.

All released engineering capabilities remain research/advisory. Equipment control
is false, automated drilling clearance is false, and no error-free or field
performance guarantee is made.
