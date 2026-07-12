@echo off
REM Run Cyber Threat Simulator Dashboard
REM Script ini menjalankan Streamlit dashboard dari direktori manapun

cd /d "%~dp0.."
echo Starting Cyber Threat Simulator Dashboard...
echo Dashboard akan terbuka di: http://localhost:8501
echo.
streamlit run src\scripts\streamlit_dashboard.py --logger.level=error
pause
