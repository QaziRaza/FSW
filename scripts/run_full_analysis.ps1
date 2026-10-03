$ErrorActionPreference = "Stop"

$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if ($env:PAPER1_PYTHON) {
    $python = $env:PAPER1_PYTHON
} elseif (Test-Path -LiteralPath $bundledPython) {
    $python = $bundledPython
} else {
    $python = "python"
}

$steps = @(
    "src/build_dataset.py",
    "src/validate_data.py",
    "src/analyse_primary.py",
    "src/analyse_replication.py",
    "src/analyse_exploratory.py",
    "src/analyse_macro_markers.py",
    "src/make_outputs.py",
    "src/make_exploratory_outputs.py",
    "src/validate_exploratory.py",
    "src/make_complete_analysis.py",
    "src/validate_complete_analysis.py"
)

foreach ($step in $steps) {
    Write-Host "Running $step"
    & $python $step
    if ($LASTEXITCODE -ne 0) {
        throw "Analysis step failed: $step"
    }
}

Write-Host "Full analysis and validation completed successfully."
