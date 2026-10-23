param([string]$Compiler = '')
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $buildArgs = @('build.py')
    if ($Compiler) { $buildArgs += @('--compiler', $Compiler) }
    & python @buildArgs
    if ($LASTEXITCODE) { throw 'ambe2-c build or reference tests failed' }
} finally { Pop-Location }
