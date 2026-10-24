$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
$uvPath = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE '.local/bin/uv.exe' }
& (Join-Path $PSScriptRoot 'Resolve-Python.ps1')
& $uvPath run --python $global:MigrationPython scripts/build.py
exit $LASTEXITCODE
