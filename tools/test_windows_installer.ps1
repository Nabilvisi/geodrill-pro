param([string]$Installer, [string]$EvidencePath)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not $Installer) { $Installer = Join-Path $projectRoot 'dist\GeoDrillPro-Setup.exe' }
if (-not $EvidencePath) { $EvidencePath = Join-Path $projectRoot 'docs\evidence\windows-installer-verification.json' }
$EvidencePath = [IO.Path]::GetFullPath($EvidencePath)
if (-not $EvidencePath.StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Evidence output escaped the workspace.' }
$releaseManifest = Get-Content -LiteralPath (Join-Path $projectRoot 'dist\release-manifest.json') -Raw | ConvertFrom-Json
$actualInstallerHash = (Get-FileHash -LiteralPath $Installer).Hash.ToLowerInvariant()
$manifestInstaller = $releaseManifest.assets | Where-Object { $_.name -eq 'GeoDrillPro-Setup.exe' }
if (-not $manifestInstaller -or $manifestInstaller.sha256 -ne $actualInstallerHash) { throw 'Installer does not match the verified release manifest.' }
$existingInstall = Get-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{62F7642F-0639-44F4-98F8-C36C617F9B1D}_is1' -ErrorAction SilentlyContinue
if ($existingInstall) { throw 'An existing user installation is registered; do not replace it for verification.' }
$verificationRoot = Join-Path $projectRoot ('build\installer-check-' + [guid]::NewGuid().ToString('N'))
$testInstallRoot = Join-Path $verificationRoot 'application'
$testDataRoot = Join-Path $verificationRoot 'evidence'
if (-not ([IO.Path]::GetFullPath($testInstallRoot).StartsWith($projectRoot + '\', [StringComparison]::OrdinalIgnoreCase))) { throw 'Test install target escaped the workspace.' }
if (Test-Path -LiteralPath $testInstallRoot) { throw 'Verification target already exists.' }
New-Item -ItemType Directory -Path $verificationRoot -Force | Out-Null
$installerLog = Join-Path $verificationRoot 'install.log'
$installed = Start-Process -FilePath $Installer -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/CURRENTUSER','/NOICONS','/NORESTART','/TASKS=',('/DIR="' + $testInstallRoot + '"'),('/LOG="' + $installerLog + '"')) -WindowStyle Hidden -Wait -PassThru
if ($installed.ExitCode -ne 0) { throw ('Installer failed: ' + $installed.ExitCode) }
$installedExe = Join-Path $testInstallRoot 'GeoDrillPro.exe'
if (-not (Test-Path -LiteralPath $installedExe)) { throw 'Installed executable missing.' }
$expectedHash = (Get-FileHash -LiteralPath (Join-Path $projectRoot 'dist\GeoDrillPro\GeoDrillPro.exe')).Hash
$installedHash = (Get-FileHash -LiteralPath $installedExe).Hash
if ($installedHash -ne $expectedHash) { throw 'Installed executable hash differs from the packaged build.' }
$previousDataDirectory = $env:GEODRILL_DATA_DIR
$backupArchive = Join-Path $verificationRoot 'workstation-backup.zip'
$restoredDataRoot = Join-Path $verificationRoot 'restored-evidence'
$rejectedDataRoot = Join-Path $verificationRoot 'rejected-restore'
try {
    $env:GEODRILL_DATA_DIR = $testDataRoot
    $smoke = Start-Process -FilePath $installedExe -ArgumentList '--smoke-test','--no-browser' -WindowStyle Hidden -Wait -PassThru
    if ($smoke.ExitCode -ne 0) { throw 'Installed API smoke failed before backup verification.' }
    $backup = Start-Process -FilePath $installedExe -ArgumentList @('--backup',('"' + $backupArchive + '"')) -WindowStyle Hidden -Wait -PassThru
    $receiptPath = $backupArchive + '.receipt.json'
    if ($backup.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $receiptPath)) { throw 'Packaged workstation backup failed.' }
    $backupReceipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    if ($backupReceipt.sha256 -ne (Get-FileHash -LiteralPath $backupArchive).Hash.ToLowerInvariant()) { throw 'Backup receipt hash mismatch.' }
    $rejectedRestore = Start-Process -FilePath $installedExe -ArgumentList @('--restore',('"' + $backupArchive + '"'),'--destination',('"' + $rejectedDataRoot + '"'),'--expected-sha256',('0' * 64)) -WindowStyle Hidden -Wait -PassThru
    if ($rejectedRestore.ExitCode -eq 0 -or (Test-Path -LiteralPath $rejectedDataRoot)) { throw 'Packaged restore accepted the wrong hash.' }
    $restore = Start-Process -FilePath $installedExe -ArgumentList @('--restore',('"' + $backupArchive + '"'),'--destination',('"' + $restoredDataRoot + '"'),'--expected-sha256',$backupReceipt.sha256) -WindowStyle Hidden -Wait -PassThru
    if ($restore.ExitCode -ne 0) { throw 'Packaged fresh-directory restore failed.' }
    $originalKey = Get-FileHash -LiteralPath (Join-Path $testDataRoot 'keys\server_ed25519.key')
    $restoredKey = Get-FileHash -LiteralPath (Join-Path $restoredDataRoot 'keys\server_ed25519.key')
    if ($originalKey.Hash -ne $restoredKey.Hash) { throw 'Restore did not preserve the signing identity.' }
    $restoredDatabase = Join-Path $restoredDataRoot 'geodrill.sqlite3'
    $beforeRefusedOverwrite = (Get-FileHash -LiteralPath $restoredDatabase).Hash
    $refusedOverwrite = Start-Process -FilePath $installedExe -ArgumentList @('--restore',('"' + $backupArchive + '"'),'--destination',('"' + $restoredDataRoot + '"'),'--expected-sha256',$backupReceipt.sha256) -WindowStyle Hidden -Wait -PassThru
    if ($refusedOverwrite.ExitCode -eq 0 -or (Get-FileHash -LiteralPath $restoredDatabase).Hash -ne $beforeRefusedOverwrite) { throw 'Existing restore destination was overwritten.' }
    $env:GEODRILL_DATA_DIR = $restoredDataRoot
    $restoredSmoke = Start-Process -FilePath $installedExe -ArgumentList '--smoke-test','--no-browser' -WindowStyle Hidden -Wait -PassThru
    if ($restoredSmoke.ExitCode -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $restoredDataRoot 'smoke-test.json'))) { throw 'Restored workstation failed packaged API diagnostics.' }
} finally {
    $env:GEODRILL_DATA_DIR = $previousDataDirectory
}
$smokePath = Join-Path $testDataRoot 'smoke-test.json'
if ($smoke.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $smokePath)) { throw 'Installed executable failed API/diagnostic smoke verification.' }
$marker = Join-Path $testInstallRoot 'user-created-evidence.txt'
'Retain user-created files during uninstall.' | Set-Content -LiteralPath $marker
$uninstaller = Join-Path $testInstallRoot 'unins000.exe'
$uninstalled = Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -WindowStyle Hidden -Wait -PassThru
if ($uninstalled.ExitCode -ne 0) { throw ('Uninstall failed: ' + $uninstalled.ExitCode) }
if (-not (Test-Path -LiteralPath $marker)) { throw 'Uninstall removed an additional user-created file.' }
if (-not (Test-Path -LiteralPath $smokePath)) { throw 'Uninstall removed persistent test evidence.' }
if (Test-Path -LiteralPath $installedExe) { throw 'Installed executable remained after uninstall.' }
$evidence = @{
    passed = $true
    installer_sha256 = $actualInstallerHash
    installed_executable_sha256 = $installedHash.ToLowerInvariant()
    install_exit_code = $installed.ExitCode
    smoke_exit_code = $smoke.ExitCode
    uninstall_exit_code = $uninstalled.ExitCode
    extra_user_file_preserved = $true
    persistent_evidence_preserved = $true
    packaged_backup_exit_code = $backup.ExitCode
    packaged_restore_exit_code = $restore.ExitCode
    restored_smoke_exit_code = $restoredSmoke.ExitCode
    wrong_hash_restore_rejected = $true
    existing_restore_destination_preserved = $true
    restored_signing_identity_preserved = $true
    backup_archive_sha256 = $backupReceipt.sha256
    signing_mode = $releaseManifest.signing_mode
    source_snapshot_sha256 = $releaseManifest.source_snapshot_sha256
    equipment_control = $false
    clearance_generated = $false
}
New-Item -ItemType Directory -Path (Split-Path -Parent $EvidencePath) -Force | Out-Null
$evidence | ConvertTo-Json | Set-Content -LiteralPath $EvidencePath -Encoding utf8
$evidence | ConvertTo-Json
