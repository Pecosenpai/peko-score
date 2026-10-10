$desktop = [System.IO.Path]::Combine($env:USERPROFILE, "Desktop")
$lnkPath = [System.IO.Path]::Combine($desktop, "ぺこすこあ.lnk")
$baseDir = "C:\Users\sasas\.gemini\antigravity\scratch\ow-counter"
$targetBat = [System.IO.Path]::Combine($baseDir, "run_pekoscore.bat")
$iconPath = [System.IO.Path]::Combine($baseDir, "icon.ico")

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($lnkPath)
$sc.TargetPath = $targetBat
$sc.WorkingDirectory = $baseDir
$sc.IconLocation = $iconPath
$sc.Description = "ぺこすこあ (by ぺこぺこ堂)"
$sc.Save()
Write-Host "Created successfully!"
