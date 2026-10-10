
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('C:\Users\sasas\Desktop\ぺこすこあ.lnk')
    $Shortcut.TargetPath = 'C:\Users\sasas\.gemini\antigravity\scratch\ow-counter\ぺこすこあ起動.bat'
    $Shortcut.WorkingDirectory = 'C:\Users\sasas\.gemini\antigravity\scratch\ow-counter'
    $Shortcut.IconLocation = 'C:\Users\sasas\.gemini\antigravity\scratch\ow-counter\icon.ico'
    $Shortcut.Description = 'ぺこすこあ - Overwatch 2 勝敗カウンター (by ぺこぺこ堂)'
    $Shortcut.Save()
    