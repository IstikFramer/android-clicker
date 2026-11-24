$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
$godot = "$root/.tools/bin/Godot_v4.7.2-stable_win64_console.exe"
& "$PSScriptRoot/build_native.ps1" debug
python "$PSScriptRoot/check_godot.py" --godot $godot
if ($LASTEXITCODE) { throw "Import or smoke failed" }
& "$PSScriptRoot/build_native.ps1" release
$stage = "win64-" + [guid]::NewGuid().ToString("N")
$out = "$root/dist/$stage"
New-Item -ItemType Directory -Force $out | Out-Null
$log = & $godot --headless --path "$root/godot" --export-release "Windows Desktop" "$out/SPACE-DIE.exe" 2>&1
$rc = $LASTEXITCODE
$log | Out-Host
if ($rc -or ($log -match '(SCRIPT ERROR|SHADER ERROR|ERROR):')) { throw "Godot export failed" }
Set-Content "$root/dist/.windows-export" $stage -Encoding ascii
