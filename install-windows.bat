@echo off
rem CPE Coach installer for Windows - just double-click this file.
rem It finds Python 3.9+ (and installs it for you if missing), then starts the installation wizard.
rem Add "-CheckOnly" to only check your computer without installing anything.
setlocal
set "HERE=%~dp0"
set "BRANCH=claude/clever-archimedes-ekcn2m"
if exist "%HERE%setup\bootstrap.ps1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%setup\bootstrap.ps1" %*
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $f=Join-Path $env:TEMP 'cpe-bootstrap.ps1'; Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/Kurihararyder/code-cc/%BRANCH%/setup/bootstrap.ps1' -OutFile $f; & $f %*; exit $LASTEXITCODE"
)
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo Setup did not finish ^(code %RC%^). Please copy the messages above and send them to me.
    pause
)
exit /b %RC%
