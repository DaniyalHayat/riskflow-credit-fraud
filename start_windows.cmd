@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m riskflow demo
if errorlevel 1 goto failed
start "RiskFlow" http://127.0.0.1:8000
py -3 -m riskflow serve
goto finished
:usepython
python -m riskflow demo
if errorlevel 1 goto failed
start "RiskFlow" http://127.0.0.1:8000
python -m riskflow serve
goto finished
:failed
echo Setup failed. Install Python 3.11 or later from python.org and enable Add Python to PATH.
pause
:finished
