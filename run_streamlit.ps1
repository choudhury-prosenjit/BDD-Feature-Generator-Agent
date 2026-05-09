$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $python = $pythonCmd.Source
    } else {
        $pyCmd = Get-Command py -ErrorAction SilentlyContinue
        if ($pyCmd) {
            $python = $pyCmd.Source
        }
    }
}

if (-not $python) {
    throw "Python was not found. Install Python or create the virtual environment with: python -m venv .venv"
}

& $python -m streamlit run (Join-Path $projectRoot 'app.py') @args

