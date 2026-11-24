$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
$stage = Get-Content "$root/dist/.windows-export" -Raw
$stage = $stage.Trim()
if ($stage -notmatch '^win64-[0-9a-f]{32}$') { throw "Invalid staging directory" }
$out = Join-Path "$root/dist" $stage
$zip = "$root/dist/SPACE-DIE-0.1.0-win64.zip"
$files = Get-ChildItem -Path $out -File -Recurse
foreach ($name in @("SPACE-DIE.exe", "SPACE-DIE.pck", "space_die_ext.dll")) {
    if ($name -notin $files.Name) { throw "Missing export: $name" }
}
$vswhere = "${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
$dumpbin = & $vswhere -latest -products '*' -find 'VC\Tools\MSVC\**\bin\Hostx64\x64\dumpbin.exe' | Select-Object -First 1
if (!$dumpbin) { throw "MSVC dumpbin is required to audit imports" }
foreach ($file in $files | Where-Object { $_.Extension -in ".dll", ".exe" }) {
    $deps = & $dumpbin /dependents $file.FullName
    $deps | Out-Host
    if ($LASTEXITCODE -or ($deps -match '(?i)(?:vcruntime|msvcp|concrt)\d+.*\.dll')) { throw "Review runtime imports in $file" }
}
Compress-Archive -Path "$out/*" -DestinationPath $zip -Force
$probe = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
try {
    Expand-Archive $zip -DestinationPath $probe
    Push-Location $probe
    try {
        $log = Join-Path $probe "smoke.log"
        $proc = Start-Process "./SPACE-DIE.exe" -ArgumentList @('--headless','--log-file','smoke.log','--','--verify-package') -PassThru
        if (!$proc.WaitForExit(120000)) { $proc.Kill(); throw "Packaged smoke timed out" }
        $text = Get-Content $log -Raw
        if ($proc.ExitCode -or $text -notmatch 'SPACE DIE SMOKE PASS' -or $text -match '(SCRIPT ERROR|SHADER ERROR|ERROR):') { throw "Packaged smoke failed: $text" }
    } finally { Pop-Location }
} finally { if (Test-Path $probe) { Remove-Item -Recurse -Force $probe } }
