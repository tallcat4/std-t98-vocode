param([string]$Compiler = '')
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (!$Compiler) {
        $found = Get-Command gcc -ErrorAction SilentlyContinue
        if ($found) { $Compiler = $found.Source }
        elseif (Test-Path 'C:\Strawberry\c\bin\gcc.exe') { $Compiler = 'C:\Strawberry\c\bin\gcc.exe' }
        else { throw 'Install a 64-bit MinGW C compiler and pass -Compiler PATH.' }
    }
    if (!(Test-Path pyambelib-source/src/libambe_wrapper.c)) {
        throw 'Fetch pyambelib-source first; see README for the pinned source revision.'
    }
    $vendorPath = 'pyambelib-source/vendor/mbelib-neo'
    $sources = @(Get-ChildItem -LiteralPath "$vendorPath/src" -Recurse -Filter '*.c' | Where-Object { $_.Name -notmatch '^test|_test\.c$|_dump\.c$|^main\.c$' } | ForEach-Object { $_.FullName })
    $includes = @("-I$vendorPath/include", "-I$vendorPath")
    $includes += @(Get-ChildItem -LiteralPath "$vendorPath/src" -Recurse -Filter '*.h' | ForEach-Object { $_.DirectoryName } | Sort-Object -Unique | ForEach-Object { "-I$_" })
    New-Item -ItemType Directory -Force build/pyambelib | Out-Null
    # pyambelib loads this library via ctypes; it does not use the Python C ABI.
    & $Compiler -std=gnu11 -O2 -shared -static -DMBE_STATIC @includes pyambelib-source/src/libambe_wrapper.c @sources -o build/pyambelib/_libambe.dll
    if ($LASTEXITCODE) { throw 'pyambelib compilation failed' }
    Copy-Item pyambelib-source/src/pyambelib/__init__.py build/pyambelib/__init__.py
    Write-Host 'Ready: local pyambelib backend in build/pyambelib'
} finally { Pop-Location }
