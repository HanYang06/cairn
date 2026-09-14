; SPDX-FileCopyrightText: 2026 HanYang06
; SPDX-License-Identifier: Apache-2.0
;
; Inno Setup 安装包脚本。由 tools/build.py 调用：
;   iscc /DMyAppVersion=<ver> packaging/windows/cairn.iss

#define MyAppName "Cairn"
#define MyAppPublisher "HanYang06"
#define MyAppExe "cairn.exe"

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

; packaging/windows/ -> 仓库根
#define ProjectRoot AddBackslash(SourcePath) + "..\.."

[Setup]
AppId={{816BA619-8BE8-4789-8AEA-3B335723F06B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile={#ProjectRoot}\LICENSE
OutputDir={#ProjectRoot}\dist\installer
OutputBaseFilename=Cairn-{#MyAppVersion}-win-x64-setup
SetupIconFile={#ProjectRoot}\assets\logo\cairn.ico
UninstallDisplayIcon={app}\{#MyAppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#ProjectRoot}\dist\cairn\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
