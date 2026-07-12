# Cyber Threat Simulator - Agent-Based Modeling

**Author:** Moh. Khairul Umam  
**NIM:** 202310370311448  
**Kelas:** Pemodelan dan Simulasi Data B  

Simulasi penyebaran ancaman siber melalui jaringan menggunakan Agent-Based Modeling (ABM) dengan framework Mesa. Studi kasus efektivitas intervensi Patch Management dan User Training terhadap tingkat kerentanan server.

## Struktur Proyek

```
Tugas Akhir/
├── src/                          # Source code
│   ├── __init__.py
│   ├── notebooks/
│   │   └── simulation.ipynb      # Jupyter notebook - Core ABM simulation engine
│   └── scripts/
│       └── streamlit_dashboard.py # Interactive Streamlit dashboard
├── scripts/                      # Launcher scripts
│   ├── run_dashboard.bat         # Windows launcher
│   └── run_dashboard.sh          # Linux/macOS launcher
├── data/                         # Data files
│   ├── raw/
│   │   ├── data_raw_simulasi.csv      # Raw simulation output (24,000 rows)
│   │   └── data_ringkasan_skenario.csv # Summary per run (120 rows)
│   └── processed/
│       └── data_analisis_statistik.csv # Aggregated statistics
├── figures/                      # Generated visualizations
│   ├── fig_timeseries.png
│   ├── fig_state_distribution.png
│   ├── fig_network_snapshot.png
│   ├── fig_efektivitas.png
│   └── fig_heatmap.png
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites
- Python 3.10+ (recommended 3.13)
- pip

### Virtual Environment Setup

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Verify Installation
```bash
python -c "import mesa, streamlit, pandas; print('OK')"
```

## Menjalankan

### Dashboard Streamlit

**Windows:** Double-click `scripts/run_dashboard.bat`

**Linux/macOS:** `bash scripts/run_dashboard.sh`

**Manual:**
```bash
streamlit run src/scripts/streamlit_dashboard.py
```

Dashboard akan terbuka di http://localhost:8501

### Notebook Simulasi
```bash
jupyter notebook src/notebooks/simulation.ipynb
```

### Port Conflict
```bash
streamlit run src/scripts/streamlit_dashboard.py --server.port 8502
```

## Fitur Dashboard

### Sidebar Configuration
- **JARINGAN**: Topologi (nodes, connections, initial infections)
- **DINAMIKA PENYEBARAN**: Infeksi, recovery, threat eksternal
- **INTERVENSI**: Patch & training untuk mitigasi
- **EKSEKUSI**: Durasi simulasi, jumlah runs, random seed

### Visualisasi (5 Tabs)
1. **Time-Series**: Infeksi & kerentanan over time
2. **Distribusi**: Histogram puncak infeksi Monte Carlo runs
3. **Topologi Jaringan**: Network visualization di 4 time points
4. **Heatmap**: Evolusi kerentanan per run
5. **Data Raw**: Tabel lengkap dengan download CSV

## Parameter Simulasi

| Parameter | Range | Default | Deskripsi |
|-----------|-------|---------|-----------|
| N_AGENTS | 10-200 | 50 | Jumlah node dalam jaringan |
| EDGE_PROB | 0.01-0.30 | 0.08 | Probabilitas koneksi antar node |
| BETA | 0.10-0.80 | 0.30 | Infection rate |
| GAMMA | 0.01-0.20 | 0.05 | Recovery rate |
| EPSILON | 0.001-0.05 | 0.01 | External threat rate |
| ALPHA | 0.20-1.00 | 0.60 | Patch effectiveness |
| TAU | 0.20-1.00 | 0.50 | Training effectiveness |
| N_STEPS | 50-500 | 200 | Durasi simulasi (steps) |
| N_RUNS | 1-30 | 5 | Monte Carlo runs |

## Model Arsitektur

**NodeState Enum**
- SUSCEPTIBLE: Rentan terhadap infeksi
- INFECTED: Terinfeksi ancaman siber
- PATCHED: Dilindungi dengan patch
- RECOVERED: Pulih dari infeksi

**Agent Behavior**
- Vulnerability Evolution: V(t+1) = V(t) x (1 - alpha-PL) x (1 - tau-UA) + epsilon
- Infection Logic: prob = beta x V x (1-UA) x prop_infected_neighbors
- Recovery: Natural recovery dengan rate gamma
- Interventions: Patch & User Training

## Teknologi

- **Python 3.13**
- **Mesa**: Agent-Based Modeling framework
- **Streamlit**: Interactive web dashboard
- **NetworkX**: Network topology
- **Matplotlib/Seaborn**: Visualisasi data
- **Pandas/NumPy**: Data processing
- **SciPy**: Mann-Whitney U statistical test

## Kesimpulan

Penelitian ini berhasil mengembangkan model simulasi berbasis agen (Agent-Based Modeling) untuk menganalisis propagasi ancaman siber pada jaringan server lokal dengan dua strategi intervensi utama, yaitu patch management dan user training. Melalui simulasi Monte Carlo sebanyak 30 kali ulangan pada masing-masing dari empat skenario yang diuji, diperoleh hasil bahwa intervensi patch management mampu mereduksi puncak infeksi sebesar 20.0%, intervensi user training mereduksi sebesar 13.3%, dan kombinasi keduanya memberikan reduksi paling signifikan yaitu 33.3% dibandingkan dengan skenario baseline tanpa intervensi. Seluruh perbedaan antar skenario terkonfirmasi signifikan secara statistik melalui uji Mann-Whitney U dengan nilai p < 0.001. Temuan ini membuktikan bahwa strategi keamanan berlapis (layered defense) yang menggabungkan intervensi teknis dan human-centered memberikan perlindungan yang jauh lebih efektif dibandingkan menerapkan salah satu intervensi secara terpisah. Selain itu, dashboard interaktif berbasis Streamlit yang dikembangkan memungkinkan eksplorasi parameter secara real-time dan visualisasi hasil yang komprehensif, sehingga dapat menjadi alat bantu pengambilan keputusan dalam alokasi sumber daya keamanan siber di lingkungan organisasi.

## Referensi

- Mesa Framework: https://mesa.readthedocs.io/
- Streamlit Docs: https://docs.streamlit.io/
- NetworkX: https://networkx.org/

---

**Tugas Akhir - Semester 6**
Pemodelan dan Simulasi | 2026
