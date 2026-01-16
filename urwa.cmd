@echo off
setlocal

REM URWA Brain - Command Line Interface
REM Passes all arguments to the Python CLI
REM Usage: urwa sans start -> urwa.cmd sans start -> python terminal\cli.py sans start

REM Ensure venv is active if not already
if not defined VIRTUAL_ENV (
    if exist "%~dp0venv\Scripts\activate.bat" (
        call "%~dp0venv\Scripts\activate.bat" >nul 2>&1
    )
)

python "%~dp0terminal\cli.py" %*

if "%~1"=="" pause
endlocal
