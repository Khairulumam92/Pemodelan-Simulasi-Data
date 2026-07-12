# Setup & Installation Guide

## Prerequisites
- Python 3.10+ (recommended 3.13)
- pip (Python package manager)

## 1. Virtual Environment Setup (Recommended)

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

## 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## 3. Verify Installation
```bash
python -c "import mesa, streamlit, pandas; print('✓ All packages installed')"
```

## 4. Run the Application

### Option A: Using the provided scripts (Recommended)
- **Windows**: Double-click `run_dashboard.bat`
- **Linux/macOS**: Run `bash run_dashboard.sh`

### Option B: Manual command
```bash
streamlit run src/scripts/streamlit_dashboard.py
```

### Option C: Run Jupyter Notebook (for development)
```bash
jupyter notebook src/notebooks/simulation.ipynb
```

## 5. Access Dashboard
Once running, open your browser and go to:
```
http://localhost:8501
```

## Troubleshooting

### Port already in use
If port 8501 is already in use:
```bash
streamlit run src/scripts/streamlit_dashboard.py --server.port 8502
```

### Mesa import errors
Ensure you have the latest version:
```bash
pip install --upgrade mesa
```

### Slow performance
- Reduce N_RUNS in sidebar (default 5)
- Reduce N_AGENTS in sidebar (default 50)
- Use faster CPU if available

## Project Structure Reference
```
src/              → Source code files
  ├── notebooks/  → Jupyter notebooks (simulation engine)
  └── scripts/    → Python scripts (Streamlit dashboard)
data/             → Data files
  ├── raw/        → Raw simulation output
  └── processed/  → Processed/analyzed data
results/          → Output results
  └── figures/    → Generated visualizations
docs/             → Documentation files
```

---

**Last Updated**: May 2026
