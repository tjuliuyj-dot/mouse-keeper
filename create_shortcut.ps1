$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Mouse Keeper.lnk")
$shortcut.TargetPath = "pythonw"
$shortcut.Arguments = "mouse_keeper.py"
$shortcut.WorkingDirectory = "$env:USERPROFILE\Desktop\mouseclick"
$shortcut.Description = "Mouse Keeper"
$shortcut.Save()
Write-Host "Shortcut created on Desktop!"
