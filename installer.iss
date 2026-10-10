#define MyAppName "ぺこすこあ"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "ぺこぺこ堂"
#define MyAppURL "https://github.com/Pecosenpai/peko-score"
#define MyAppExeName "PekoScore.exe"

[Setup]
AppId={{E681C3D8-7B84-48E1-9AE9-482026PEKO01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\PekoScore
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist_installer
OutputBaseFilename=PekoScore-Setup-v1.0.2
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\PekoScore\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_update_extracted"
Type: files; Name: "{app}\_peko_update.zip"
Type: files; Name: "{app}\_apply_update.bat"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ConfigFile: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    ConfigFile := ExpandConstant('{app}\config.json');
    if FileExists(ConfigFile) then
    begin
      if MsgBox('設定ファイル（勝敗スコアやキー設定）も削除して完全にアンインストールしますか？', mbConfirmation, MB_YESNO) = idYes then
      begin
        DeleteFile(ConfigFile);
        RemoveDir(ExpandConstant('{app}'));
      end;
    end
    else
    begin
      RemoveDir(ExpandConstant('{app}'));
    end;
  end;
end;
