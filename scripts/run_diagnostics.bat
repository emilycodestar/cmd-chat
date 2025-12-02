@echo off
setlocal enabledelayedexpansion

rem Resolve repository root from the scripts directory
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI\"
set "VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    set "PYTHON=%VENV_PYTHON%"
) else (
    set "PYTHON=python"
    echo [INFO] Using Python from PATH because .venv interpreter was not found.
)

pushd "%PROJECT_ROOT%" >nul

call :run_script check_messages || goto :error
call :run_script debug_messages || goto :error
call :run_script test_security || goto :error

echo.
echo All diagnostic scripts finished successfully.
popd >nul
exit /b 0

:run_script
set "SCRIPT_NAME=%~1"
echo.
echo === Running %SCRIPT_NAME%.py ===
"%PYTHON%" "test\%SCRIPT_NAME%.py"
exit /b %errorlevel%

:error
echo.
echo Script %SCRIPT_NAME%.py failed with exit code %errorlevel%.
popd >nul
exit /b 1
