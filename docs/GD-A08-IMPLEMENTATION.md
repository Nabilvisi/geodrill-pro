# GD-A08 — local recovery and distribution

Current source adds tools/backup_restore.py and desktop --backup/--restore commands.
Research-3 contains these commands and passed actual installed-EXE backup/restore,
wrong-hash refusal, fresh restore, existing-destination preservation, signer-key
preservation and restored API smoke checks. Windows and Ubuntu each passed 602
tests at c4037d21ed3313ef21a335882a1330b24f00c41e.
See [published recovery evidence](evidence/published-recovery-verification.json).

Stop the application before backup. A whole-workstation snapshot uses SQLite's backup
API, including committed WAL records, and holds a database write lock while copying
raw sources, normalized Parquet, reports and keys. It checks database/foreign-key
integrity, existing source/report/revision/audit hashes, member hashes and archive
identity. Changed source files refuse publication. Limits: 20,000 files and 2 GiB
uncompressed. Existing backup files are never replaced.

Restore requires a retained SHA-256 and a new directory. Unsafe/duplicate paths,
symbolic links, unexpected members, hash/size changes, unsupported schema and existing
destinations are rejected. Backups contain password hashes, session state and the
attestation private key; keep them in a protected local location. Checksums establish
identity to a retained value, not independent signer trust.

Source commands, from the repository:

```powershell
.venv\Scripts\python.exe tools/backup_restore.py backup --source data --archive build/workstation-backup.zip
.venv\Scripts\python.exe tools/backup_restore.py restore --archive build/workstation-backup.zip --destination build/restored-data --expected-sha256 <retained-sha256>
```

Desktop builds containing this change support:

```powershell
$geodrillBackup = Start-Process -FilePath '.\GeoDrillPro.exe' -ArgumentList '--backup','C:\GeoDrillBackups\workstation.zip' -WindowStyle Hidden -Wait -PassThru
if ($geodrillBackup.ExitCode -ne 0) { throw 'Backup refused; do not continue' }
$geodrillReceipt = Get-Content -Raw C:\GeoDrillBackups\workstation.zip.receipt.json | ConvertFrom-Json
$geodrillRestore = Start-Process -FilePath '.\GeoDrillPro.exe' -ArgumentList '--restore','C:\GeoDrillBackups\workstation.zip','--destination','C:\GeoDrillRestored\data','--expected-sha256',$geodrillReceipt.sha256 -WindowStyle Hidden -Wait -PassThru
if ($geodrillRestore.ExitCode -ne 0) { throw 'Restore refused; retain the original data directory' }
```

Set GEODRILL_DATA_DIR to the restored directory before normal startup. Recovery commands
do not start or migrate the API. Pending migrations now execute as one transaction:
failure rolls back DDL, changed data and user_version. No destructive down-migration
is introduced. For a committed upgrade, retain the old package and restore its
pre-upgrade snapshot into a new directory.

Project-scoped .gdpz exchange is separate in Store.export_bundle/restore_bundle and
the API. Team restore requires an administrator because archives include identities.
It retains supplied source history in an explicit import record and appends new
calculation.restored records so saved studies reopen against the new audit chain.
Original programme signatures and supplied public keys survive re-export; supplied
keys are not independent trust. HTTP imports remain limited to 2 MiB; full local
backup/restore serves larger recovery.

Tests: test_backup_restore.py, test_project_recovery.py, test_migrations.py and the
connected workflow. The release installer check exercises actual packaged backup,
wrong-hash rejection, fresh restore, existing-destination refusal, signer preservation
and restored API diagnostics.

Remaining scope: automatic update/channel selection and binary rollback, trusted
publisher signing, broader crash/disk-full fault injection and clean-machine/operator
acceptance. These requirements remain open.

