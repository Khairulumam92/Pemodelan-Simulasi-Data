#!/bin/bash
# Run Cyber Threat Simulator Dashboard
# Script ini menjalankan Streamlit dashboard dari direktori manapun

cd "$(dirname "$0")/.."
echo "Starting Cyber Threat Simulator Dashboard..."
echo "Dashboard akan terbuka di: http://localhost:8501"
echo ""
streamlit run src/scripts/streamlit_dashboard.py --logger.level=error
