@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -m streamlit run "%PROJECT_ROOT%app.py" %*
    exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
    python -m streamlit run "%PROJECT_ROOT%app.py" %*
    exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -m streamlit run "%PROJECT_ROOT%app.py" %*
    exit /b %errorlevel%
)

echo Python was not found. Install Python or create the virtual environment with: python -m venv .venv
exit /b 1

