import os

def create_desktop_shortcut():
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    base_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter"
    target_bat = os.path.join(base_dir, "ぺこすこあ起動.bat")
    ico_path = os.path.join(base_dir, "icon.ico")
    lnk_path = os.path.join(desktop, "ぺこすこあ.lnk")
    
    # PowerShellスクリプトでショートカット作成
    ps_cmd = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{lnk_path}')
    $Shortcut.TargetPath = '{target_bat}'
    $Shortcut.WorkingDirectory = '{base_dir}'
    $Shortcut.IconLocation = '{ico_path}'
    $Shortcut.Description = 'ぺこすこあ - Overwatch 2 勝敗カウンター (by ぺこぺこ堂)'
    $Shortcut.Save()
    """
    
    ps_file = os.path.join(base_dir, "create_lnk.ps1")
    with open(ps_file, "w", encoding="utf-8") as f:
        f.write(ps_cmd)
        
    os.system(f'powershell -ExecutionPolicy Bypass -File "{ps_file}"')
    print("Desktop shortcut created successfully!")

if __name__ == "__main__":
    create_desktop_shortcut()
