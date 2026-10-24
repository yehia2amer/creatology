$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
$uvPath = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE '.local/bin/uv.exe' }
if (-not (Test-Path -LiteralPath $uvPath)) { throw 'Install uv from https://docs.astral.sh/uv/getting-started/installation/ then run this launcher again.' }
& (Join-Path $PSScriptRoot 'Resolve-Python.ps1')
$pythonPath = $global:MigrationPython
if (-not (Test-Path -LiteralPath '.tools/zola.exe')) { & $uvPath run --python $pythonPath scripts/bootstrap.py; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
Write-Host "Select this repository in Sveltia: $PSScriptRoot"
Write-Host 'Admin: http://localhost:1111/admin/  |  Preview: http://localhost:1111/'
& $uvPath run --python $pythonPath scripts/dev.py
exit $LASTEXITCODE
