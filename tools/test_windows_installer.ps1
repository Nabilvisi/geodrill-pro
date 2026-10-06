param([string]$Installer)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not $Installer) { $Installer = Join-Path $projectRoot 'dist\GeoDrillPro-Setup.exe' }
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
try {
    $env:GEODRILL_DATA_DIR = $testDataRoot
    $smoke = Start-Process -FilePath $installedExe -ArgumentList '--smoke-test','--no-browser' -WindowStyle Hidden -Wait -PassThru
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
    installer_sha256 = (Get-FileHash -LiteralPath $Installer).Hash.ToLowerInvariant()
    installed_executable_sha256 = $installedHash.ToLowerInvariant()
    install_exit_code = $installed.ExitCode
    smoke_exit_code = $smoke.ExitCode
    uninstall_exit_code = $uninstalled.ExitCode
    extra_user_file_preserved = $true
    persistent_evidence_preserved = $true
    signing_mode = 'unsigned_research'
    equipment_control = $false
    clearance_generated = $false
}
$evidence | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $projectRoot 'docs\evidence\windows-installer-verification.json') -Encoding utf8
$evidence | ConvertTo-Json
