#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif
#ifndef OutputName
  #define OutputName "PlumeSetup"
#endif

[Setup]
AppName=Plume
AppVersion={#AppVersion}
AppPublisher=atef5-in
AppPublisherURL=https://github.com/atef5-in/Plume
DefaultDirName={autopf}\Plume
DefaultGroupName=Plume
OutputBaseFilename={#OutputName}
OutputDir=Output
Compression=lzma
SolidCompression=yes
; No admin rights required — installs per-user
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=Plume
UninstallDisplayIcon={app}\plume.exe
SetupIconFile=plume.ico

[Files]
Source: "dist\plume\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Plume"; Filename: "{app}\plume.exe"; IconFilename: "{app}\_internal\plume.ico"
Name: "{group}\Désinstaller Plume"; Filename: "{uninstallexe}"

[Registry]
; Launch Plume automatically at Windows login
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "Plume"; \
  ValueData: """{app}\plume.exe"""; Flags: uninsdeletevalue

[Run]
; Offer to launch Plume immediately after install
Filename: "{app}\plume.exe"; Description: "Lancer Plume maintenant"; \
  Flags: nowait postinstall skipifsilent
