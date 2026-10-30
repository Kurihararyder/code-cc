@echo off
rem CPE Coach installer for Windows - just double-click this file.
rem It finds Python 3.9+ (and installs it for you if missing), then starts the installation wizard.
rem Add "-CheckOnly" to only check your computer without installing anything.
rem (No parenthesised blocks on purpose: a folder name such as "Downloads (1)" would break them.)
setlocal
set "HERE=%~dp0"
set "BRANCH=claude/clever-archimedes-ekcn2m"
if exist "%HERE%setup\bootstrap.ps1" goto local
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $f=Join-Path $env:TEMP 'cpe-bootstrap.ps1'; Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/Kurihararyder/code-cc/%BRANCH%/setup/bootstrap.ps1' -OutFile $f; & $f %*; exit $LASTEXITCODE"
goto finished
:local
powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%setup\bootstrap.ps1" %*
:finished
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" exit /b 0
echo.
echo Setup did not finish ^(code %RC%^). Please copy the messages above and send them to me.
pause
exit /b %RC%
