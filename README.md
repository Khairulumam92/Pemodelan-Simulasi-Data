# Cyber Threat Simulator - Agent-Based Modeling

Simulasi penyebaran ancaman siber melalui jaringan menggunakan Agent-Based Modeling (ABM) dengan framework Mesa.

## 📁 Struktur Proyek

```
Tugas Akhir/
├── src/                          # Source code
│   ├── notebooks/
│   │   └── simulation.ipynb      # Jupyter notebook - Core ABM simulation engine
│   └── scripts/
│       └── streamlit_dashboard.py # Interactive Streamlit dashboard
├── data/                         # Data files
│   ├── raw/
│   │   ├── data_raw_simulasi.csv
│   │   └── data_ringkasan_skenario.csv
│   └── processed/
│       └── data_analisis_statistik.csv
├── results/                      # Output results
│   └── figures/
│       ├── fig_timeseries.png
│       ├── fig_state_distribution.png
│       ├── fig_network_snapshot.png
│       ├── fig_efektivitas.png
│       └── fig_heatmap.png
├── assets/                       # Asset files
├── docs/                         # Documentation
└── README.md                     # File ini
```

## 🚀 Cara Menjalankan

### 1. Setup Environment
```bash
pip install numpy pandas networkx matplotlib seaborn tqdm scipy mesa streamlit
```

### 2. Jalankan Notebook Simulasi
```bash
jupyter notebook src/notebooks/simulation.ipynb
```

### 3. Jalankan Dashboard Streamlit
```bash
streamlit run src/scripts/streamlit_dashboard.py
```
Dashboard akan terbuka di: http://localhost:8501

## 📊 Fitur Dashboard

### Sidebar Configuration
- **JARINGAN**: Konfigurasi topologi (nodes, connections, initial infections)
- **DINAMIKA PENYEBARAN**: Parameter infeksi, recovery, threat eksternal
- **INTERVENSI**: Strategi patch & training untuk mitigasi
- **EKSEKUSI**: Durasi simulasi, jumlah runs, random seed

### Visualisasi (5 Tabs)
1. **Time-Series**: Tracking infeksi & kerentanan over time
2. **Distribusi**: Histogram puncak infeksi dari all Monte Carlo runs
3. **Topologi Jaringan**: Network visualization di 4 time points
4. **Heatmap**: Evolusi kerentanan per run
5. **Data Raw**: Tabel lengkap dengan download CSV

## 🎨 Design Features
- **Dark Theme**: Warna profesional yang carefully curated
- **Color Scheme**: 14 warna distinct tanpa overlap
- **Responsive**: Desain yang adaptif dan interaktif
- **Data Export**: Download hasil simulasi dalam format CSV

## 📝 Parameter Simulasi

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

## 📈 Output Data

### raw/
- `data_raw_simulasi.csv`: Data mentah setiap step dari setiap run (24,000 rows)
- `data_ringkasan_skenario.csv`: Ringkasan per run (120 rows)

### processed/
- `data_analisis_statistik.csv`: Statistik agregat per skenario

### figures/
- Time-series plot
- State distribution
- Network snapshots
- Efektivitas intervensi
- Heatmap kerentanan

## 🔬 Model Architecture

**NodeState Enum**
- SUSCEPTIBLE: Rentan terhadap infeksi
- INFECTED: Terinfeksi ancaman siber
- PATCHED: Dilindungi dengan patch
- RECOVERED: Pulih dari infeksi

**Agent Behavior**
- Vulnerability Evolution: V(t+1) = V(t) × (1 - α·PL) × (1 - τ·UA) + ε
- Infection Logic: prob = β × V × (1-UA) × prop_infected_neighbors
- Recovery: Natural recovery dengan rate γ
- Interventions: Patch & User Training

## 👨‍💻 Teknologi

- **Python 3.13**
- **Mesa**: Agent-Based Modeling framework
- **Streamlit**: Interactive web dashboard
- **NetworkX**: Network topology
- **Matplotlib/Seaborn**: Visualisasi data
- **Pandas/NumPy**: Data processing

## 📚 Referensi

- Mesa Framework: https://mesa.readthedocs.io/
- Streamlit Docs: https://docs.streamlit.io/
- NetworkX: https://networkx.org/

---

**Tugas Akhir - Semester 6**  
Pemodelan Sistem | 2026
