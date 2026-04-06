#define MyAppName "StudyFlow Device Lock"
#ifndef APP_VERSION
	#define APP_VERSION "0.2.1"
#endif
#define MyAppVersion APP_VERSION
#define MyAppPublisher "StudyFlow"
#define MyAppExeName "studyflow-lock.exe"

[Setup]
AppId={{2F019A98-0E0D-4D20-9DA2-C3FFB6D93311}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\StudyFlow Device Lock
DefaultGroupName=StudyFlow Device Lock
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=StudyFlow-Lock-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "startup"; Description: "Windows起動時に自動起動する"; GroupDescription: "追加オプション:"; Flags: unchecked

[Files]
Source: "..\dist\studyflow-lock.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist
Source: "..\whitelist.json"; DestDir: "{app}"; Flags: onlyifdoesntexist

[Icons]
Name: "{autoprograms}\StudyFlow Device Lock"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\StudyFlow Device Lock"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Description: "StudyFlow Device Lock を起動"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "StudyFlowDeviceLock"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: startup
