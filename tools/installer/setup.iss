; Inno Setup Script for GeoDrill Pro Engineering Workstation
; Per-user installer. Packaging does not establish engineering qualification.

#define MyAppName "GeoDrill Pro Engineering Workstation"
#define MyAppVersion "0.9.0-alpha.2"
#define MyAppPublisher "GeoDrill Pro Engineering Team"
#define MyAppURL "https://geodrill-pro.streamlit.app/"
#define MyAppExeName "GeoDrillPro.exe"

[Setup]
; Basic Application Information
AppId={{62F7642F-0639-44F4-98F8-C36C617F9B1D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Destination Directories
DefaultDirName={autopf}\GeoDrillPro
DefaultGroupName=GeoDrill Pro
AllowNoIcons=yes
DisableProgramGroupPage=yes

; Output Configuration
OutputDir=..\..\dist
OutputBaseFilename=GeoDrillPro-Setup
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression & Architecture
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
PrivilegesRequired=lowest

; Wizard Appearance
WizardStyle=modern
ShowLanguageDialog=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\GeoDrillPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Automatic %APPDATA%/GeoDrillPro directory initialization for user evidence and project storage
Name: "{userappdata}\GeoDrillPro"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\GeoDrill Pro"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; Inno removes only installed files. Preserve additional user files on uninstall.
