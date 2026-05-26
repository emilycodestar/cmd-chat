@echo off
setlocal

pushd "%~dp0" >nul

set "PYTHON_BIN="
where py >nul 2>&1 && set "PYTHON_BIN=py -3"
if not defined PYTHON_BIN (
    where python >nul 2>&1 && set "PYTHON_BIN=python"
)

if not defined PYTHON_BIN (
    echo Python 3 was not found on PATH.
    popd >nul
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    call %PYTHON_BIN% -m venv venv
    if errorlevel 1 goto :fail
)

if not exist "venv\.cmd-chat-deps-installed" (
    call "venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :fail
    call "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
    type nul > "venv\.cmd-chat-deps-installed"
)

if "%~1"=="" (
    echo Usage:
    echo   start.bat serve 0.0.0.0 3000 --password mysecret
    echo   start.bat connect SERVER_IP 3000 username mysecret
    popd >nul
    exit /b 0
)

call "venv\Scripts\python.exe" cmd_chat.py %*
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
exit /b %EXIT_CODE%

:fail
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
exit /b %EXIT_CODE%
