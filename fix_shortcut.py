import os
import subprocess

def fix_shortcut():
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    
    # 文字化けしている古いlnkを削除
    for f in os.listdir(desktop):
        if f.endswith(".lnk") and ("32314" in str([ord(c) for c in f]) or "ow" in f.lower()):
            try:
                os.remove(os.path.join(desktop, f))
            except Exception:
                pass

    base_dir = r"C:\Users\sasas\.gemini\antigravity\scratch\ow-counter"
    target_bat = os.path.join(base_dir, "run_pekoscore.bat")
    icon_path = os.path.join(base_dir, "icon.ico")
    lnk_name = "PekoScore.lnk"  # 英語名で作成
    lnk_path = os.path.join(desktop, lnk_name)

    ps_script = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{lnk_path}")
    $Shortcut.TargetPath = "{target_bat}"
    $Shortcut.WorkingDirectory = "{base_dir}"
    $Shortcut.IconLocation = "{icon_path}"
    $Shortcut.Description = "PekoScore"
    $Shortcut.Save()
    """
    
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True)
    
    # Pythonから直接「ぺこすこあ.lnk」にリネーム（OS標準のUnicodeリネーム）
    final_lnk_path = os.path.join(desktop, "ぺこすこあ.lnk")
    if os.path.exists(final_lnk_path):
        os.remove(final_lnk_path)
    os.rename(lnk_path, final_lnk_path)
    print("Fixed and created cleanly:", final_lnk_path)

if __name__ == "__main__":
    fix_shortcut()
