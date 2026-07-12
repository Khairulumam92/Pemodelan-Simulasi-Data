# Quick Reference Guide

## 🚀 Quick Start (3 Steps)

```bash
# 1. Install dependencies (pertama kali saja)
pip install -r requirements.txt

# 2. Run dashboard
streamlit run src/scripts/streamlit_dashboard.py

# 3. Open browser
http://localhost:8501
```

## 📦 Struktur Folder Penjelasan

| Folder | Isi | Deskripsi |
|--------|-----|-----------|
| `src/notebooks` | `.ipynb` | Jupyter notebook dengan simulation engine |
| `src/scripts` | `.py` | Python scripts (dashboard Streamlit) |
| `data/raw` | `.csv` | Raw data dari simulation runs |
| `data/processed` | `.csv` | Data yang sudah dianalisis |
| `results/figures` | `.png` | Visualisasi output |
| `docs` | `.md` | Dokumentasi (setup guide, etc) |
| `assets` | Mixed | Asset files |

## 🎮 Menggunakan Dashboard

### Parameter Sidebar
1. **JARINGAN** - Network configuration
   - n_agents: 10-200 nodes
   - edge_prob: 0.01-0.30 connection probability
   - initial_infected: 1-20 starting infections

2. **DINAMIKA PENYEBARAN** - Spreading dynamics
   - beta: 0.10-0.80 (infection rate)
   - gamma: 0.01-0.20 (recovery rate)
   - epsilon: 0.001-0.05 (external threat)

3. **INTERVENSI** - Mitigation strategies
   - use_patch: Enable patching
   - use_training: Enable user training
   - patch_threshold: 0.30-1.00

4. **EKSEKUSI** - Simulation settings
   - n_steps: 50-500 duration
   - n_runs: 1-30 Monte Carlo runs
   - random_seed: For reproducibility

### 5 Visualization Tabs
- **Time-Series**: Infection & vulnerability over time
- **Distribusi**: Distribution of peak infections
- **Topologi Jaringan**: Network snapshots at 4 time points
- **Heatmap**: Vulnerability evolution per run
- **Data Raw**: Full data table + CSV download

## 🔧 Common Commands

```bash
# Run with custom port
streamlit run src/scripts/streamlit_dashboard.py --server.port 8502

# Run notebook
jupyter notebook src/notebooks/simulation.ipynb

# Install specific package
pip install <package_name>

# List all packages
pip list

# Upgrade package
pip install --upgrade <package_name>

# Stop Streamlit
# Ctrl+C in terminal
```

## 📊 Data Files

### Input/Output Locations
- **Raw Data**: `data/raw/` (24,000 rows total)
- **Processed**: `data/processed/` (statistics)
- **Figures**: `results/figures/` (PNG images)
- **Export**: Download directly from dashboard

### Filenames
- `data_raw_simulasi.csv` - Full simulation data
- `data_ringkasan_skenario.csv` - Summary per run
- `data_analisis_statistik.csv` - Aggregated stats

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8501 in use | `streamlit run ... --server.port 8502` |
| Module not found | `pip install -r requirements.txt` |
| Slow simulation | Reduce n_runs or n_agents in sidebar |
| Dashboard not loading | Wait 30 seconds, refresh browser |
| File not found errors | Check you're in root directory |

## 📚 File Descriptions

| File | Purpose |
|------|---------|
| `README.md` | Full project documentation |
| `requirements.txt` | All Python dependencies |
| `PROJECT_STRUCTURE.txt` | Folder organization info |
| `.gitignore` | Git configuration |
| `run_dashboard.bat` | Windows quick launcher |
| `run_dashboard.sh` | Linux/Mac quick launcher |
| `docs/SETUP.md` | Detailed setup guide |

## 💾 Saving Your Work

```bash
# Save data from dashboard
# → Click "📥 Download CSV" in Data Raw tab
# → File saved as: cyber_threat_sim_YYYYMMDD_HHMMSS.csv
```

## 🔬 Model Parameters

### Default Values
```python
N_AGENTS = 50           # nodes
EDGE_PROB = 0.08        # connection probability
BETA = 0.30            # infection rate
GAMMA = 0.05           # recovery rate
EPSILON = 0.01         # external threat
ALPHA = 0.60           # patch effectiveness
TAU = 0.50             # training effectiveness
N_STEPS = 200          # simulation duration
N_RUNS = 5             # Monte Carlo runs
```

### Formulas
```
Vulnerability: V(t+1) = V(t) × (1 - α×PL) × (1 - τ×UA) + ε
Infection Probability: p = β × V × (1-UA) × prop_neighbors_infected
```

## 🎨 Color Scheme

| Color | Hex | Usage |
|-------|-----|-------|
| Blue | #1f77b4 | Primary/Susceptible |
| Red | #ff5252 | Infected |
| Green | #66bb6a | Patched/Success |
| Cyan | #29b6f6 | Recovered/Info |
| Amber | #ffa726 | Warning/Vulnerability |
| Dark | #0a0e27 | Background |

## 📞 Support

For issues:
1. Check `docs/SETUP.md` for installation help
2. Review `README.md` for features overview
3. Check terminal output for error messages
4. Verify all files are in correct folders

---

**Last Updated**: May 2026  
**Version**: 2.0 (Reorganized Structure)
