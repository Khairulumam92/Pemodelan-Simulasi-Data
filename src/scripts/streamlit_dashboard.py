import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from enum import Enum
from tqdm import tqdm
from scipy import stats
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# ║  CUSTOM SCHEDULER & COMPONENTS  ║
# ═══════════════════════════════════════════════════════════════════════════════

from mesa import Agent, Model
from mesa.datacollection import DataCollector
import random


class RandomActivation:
    """Simple random activation scheduler."""
    def __init__(self, model):
        self.model = model
        self.agents = []
        self.time = 0
    
    def add(self, agent):
        self.agents.append(agent)
    
    def remove(self, agent):
        if agent in self.agents:
            self.agents.remove(agent)
    
    def step(self):
        """Shuffle agents and call step on each."""
        shuffled = self.agents.copy()
        random.shuffle(shuffled)
        for agent in shuffled:
            agent.step()
        self.time += 1


# ═══════════════════════════════════════════════════════════════════════════════
# ║  STATE & COLORS  ║
# ═══════════════════════════════════════════════════════════════════════════════

class NodeState(Enum):
    SUSCEPTIBLE = 'S'
    INFECTED    = 'I'
    PATCHED     = 'P'
    RECOVERED   = 'R'

# Update setelah COLOR_SCHEME didefinisikan
STATE_COLORS_MAP = {
    'susceptible': '#4d9ef6',      # Biru cerah
    'infected':    '#ff5252',      # Merah cerah
    'patched':     '#66bb6a',      # Hijau
    'recovered':   '#29b6f6',      # Cyan cerah
}


# ═══════════════════════════════════════════════════════════════════════════════
# ║  SERVER NODE CLASS  ║
# ═══════════════════════════════════════════════════════════════════════════════

class ServerNode(Agent):
    """Agen yang merepresentasikan satu server dalam jaringan lokal."""

    def __init__(self, unique_id, model, initial_state=NodeState.SUSCEPTIBLE):
        super().__init__(model)
        self.unique_id = unique_id
        self.state = initial_state
        self.vulnerability  = self.random.uniform(0.4, 0.9)
        self.patch_level    = self.random.uniform(0.0, 0.2)
        self.user_awareness = self.random.uniform(0.1, 0.4)

    def update_vulnerability(self):
        """Update kerentanan: V(t+1) = V(t) × (1 - α·PL) × (1 - τ·UA) + ε"""
        self.vulnerability = (
            self.vulnerability
            * (1 - self.model.alpha * self.patch_level)
            * (1 - self.model.tau   * self.user_awareness)
            + self.model.epsilon
        )
        self.vulnerability = float(np.clip(self.vulnerability, 0.0, 1.0))

    def try_infect(self):
        """Cek apakah node bisa terinfeksi dari tetangga atau ancaman eksternal."""
        if self.state != NodeState.SUSCEPTIBLE:
            return

        neighbors = list(self.model.graph.neighbors(self.unique_id))

        if not neighbors:
            if self.random.random() < self.model.epsilon * self.vulnerability:
                self.state = NodeState.INFECTED
            return

        infected_neighbors = [
            n for n in neighbors
            if self.model.agents_dict[n].state == NodeState.INFECTED
        ]

        if not infected_neighbors:
            if self.random.random() < self.model.epsilon * self.vulnerability:
                self.state = NodeState.INFECTED
            return

        prop = len(infected_neighbors) / len(neighbors)
        p_infect = float(np.clip(
            self.model.beta * self.vulnerability * (1 - self.user_awareness) * prop,
            0.0, 1.0
        ))
        if self.random.random() < p_infect:
            self.state = NodeState.INFECTED

    def try_recover(self):
        """Node terinfeksi bisa pulih secara alami dengan probabilitas γ."""
        if self.state == NodeState.INFECTED:
            if self.random.random() < self.model.gamma:
                self.state = NodeState.RECOVERED
                self.vulnerability = max(0.0, self.vulnerability - 0.08)

    def apply_patch(self):
        """Terapkan patch: ubah state ke PATCHED dan naikkan patch_level."""
        if self.state in [NodeState.SUSCEPTIBLE, NodeState.RECOVERED]:
            self.state = NodeState.PATCHED
            self.patch_level = min(1.0, self.patch_level + 0.55)

    def apply_training(self):
        """Tingkatkan user_awareness melalui sesi pelatihan."""
        self.user_awareness = min(1.0, self.user_awareness + 0.10)

    def step(self):
        """Satu langkah waktu: update vulnerability → cek infeksi → cek pemulihan."""
        self.update_vulnerability()
        self.try_infect()
        self.try_recover()


# ═══════════════════════════════════════════════════════════════════════════════
# ║  CYBER THREAT MODEL  ║
# ═══════════════════════════════════════════════════════════════════════════════

class CyberThreatModel(Model):
    """Model ABM penyebaran ancaman siber pada jaringan server lokal."""

    def __init__(
        self,
        n_agents=50,
        initial_infected=5,
        edge_prob=0.08,
        beta=0.30,
        gamma=0.05,
        epsilon=0.01,
        alpha=0.60,
        tau=0.50,
        use_patch=False,
        use_training=False,
        patch_proactive=False,
        training_interval=10,
        patch_threshold=0.70,
        seed=None,
    ):
        super().__init__()
        if seed is not None:
            self.random.seed(seed)
            np.random.seed(seed)

        self.n_agents          = n_agents
        self.beta              = beta
        self.gamma             = gamma
        self.epsilon           = epsilon
        self.alpha             = alpha
        self.tau               = tau
        self.use_patch         = use_patch
        self.use_training      = use_training
        self.patch_proactive   = patch_proactive
        self.training_interval = training_interval
        self.patch_threshold   = patch_threshold

        self.graph    = nx.erdos_renyi_graph(n=n_agents, p=edge_prob, seed=seed)
        self.schedule = RandomActivation(self)

        initial_infected_ids = set(self.random.sample(range(n_agents), initial_infected))

        self.agents_dict = {}
        for node_id in range(n_agents):
            init_state = (
                NodeState.INFECTED
                if node_id in initial_infected_ids
                else NodeState.SUSCEPTIBLE
            )
            agent = ServerNode(node_id, self, initial_state=init_state)
            self.schedule.add(agent)
            self.agents_dict[node_id] = agent

        self.datacollector = DataCollector(
            model_reporters={
                'n_susceptible'     : lambda m: sum(1 for a in m.agents_dict.values() if a.state == NodeState.SUSCEPTIBLE),
                'n_infected'        : lambda m: sum(1 for a in m.agents_dict.values() if a.state == NodeState.INFECTED),
                'n_patched'         : lambda m: sum(1 for a in m.agents_dict.values() if a.state == NodeState.PATCHED),
                'n_recovered'       : lambda m: sum(1 for a in m.agents_dict.values() if a.state == NodeState.RECOVERED),
                'avg_vulnerability' : lambda m: float(np.mean([a.vulnerability  for a in m.agents_dict.values()])),
                'avg_user_awareness': lambda m: float(np.mean([a.user_awareness for a in m.agents_dict.values()])),
            }
        )

    def apply_patch_intervention(self):
        if not self.use_patch:
            return
        for agent in self.agents_dict.values():
            if self.patch_proactive:
                if agent.state in [NodeState.SUSCEPTIBLE, NodeState.RECOVERED]:
                    agent.apply_patch()
            else:
                if (agent.state in [NodeState.SUSCEPTIBLE, NodeState.RECOVERED]
                        and agent.vulnerability > self.patch_threshold):
                    agent.apply_patch()

    def apply_training_intervention(self):
        if not self.use_training:
            return
        t = self.schedule.time
        if t > 0 and t % self.training_interval == 0:
            for agent in self.agents_dict.values():
                agent.apply_training()

    def step(self):
        self.datacollector.collect(self)
        self.apply_patch_intervention()
        self.apply_training_intervention()
        self.schedule.step()


# ═══════════════════════════════════════════════════════════════════════════════
# ║  SIMULATION RUNNER  ║
# ═══════════════════════════════════════════════════════════════════════════════

def run_single_simulation(model_kwargs, n_steps, progress_placeholder=None):
    """Jalankan satu simulasi dan kembalikan hasil mentah."""
    seed  = model_kwargs.get('seed', 42)
    model = CyberThreatModel(seed=seed, **{k: v for k, v in model_kwargs.items() if k != 'seed'})
    
    raw_records = []
    peak_infected = 0
    peak_step = 0
    recovery_step = n_steps
    RECOVERY_THR = 0.10
    N_AGENTS = model_kwargs.get('n_agents', 50)

    for step in range(n_steps):
        model.step()
        data  = model.datacollector.get_model_vars_dataframe().iloc[-1]
        n_inf = int(data['n_infected'])

        if n_inf > peak_infected:
            peak_infected = n_inf
            peak_step = step + 1

        if step > 10 and n_inf / N_AGENTS < RECOVERY_THR and recovery_step == n_steps:
            recovery_step = step + 1

        raw_records.append({
            'langkah'             : step + 1,
            'n_susceptible'       : int(data['n_susceptible']),
            'n_infected'          : n_inf,
            'n_patched'           : int(data['n_patched']),
            'n_recovered'         : int(data['n_recovered']),
            'rata_vulnerability'  : round(float(data['avg_vulnerability']), 4),
            'rata_user_awareness' : round(float(data['avg_user_awareness']), 4),
        })

        if progress_placeholder:
            progress_placeholder.progress(step / n_steps)

    final = model.datacollector.get_model_vars_dataframe().iloc[-1]
    
    return {
        'data': pd.DataFrame(raw_records),
        'peak_infected': peak_infected,
        'peak_step': peak_step,
        'recovery_step': recovery_step,
        'infeksi_akhir': int(final['n_infected']),
        'vulnerability_akhir': round(float(final['avg_vulnerability']), 4),
        'user_awareness_akhir': round(float(final['avg_user_awareness']), 4),
        'graph': model.graph,
        'model': model,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ║  STREAMLIT PAGE CONFIG  ║
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Cyber Threat Simulator Dashboard",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# ║  CUSTOM STYLING & COLOR SCHEME  ║
# ═══════════════════════════════════════════════════════════════════════════════

COLOR_SCHEME = {
    'primary':      '#1f77b4',      # Biru deep
    'secondary':    '#ff7f0e',      # Orange
    'success':      '#2ca02c',      # Hijau
    'danger':       '#d62728',      # Merah
    'warning':      '#ff9800',      # Amber
    'info':         '#17a2b8',      # Cyan
    'dark_bg':      '#0a0e27',      # Dark bg
    'card_bg':      '#141829',      # Card bg
    'text_light':   '#e8eaed',      # Light text
    'border':       '#2d3142',      # Border
    'susceptible':  '#4d9ef6',      # Biru cerah
    'infected':     '#ff5252',      # Merah cerah
    'patched':      '#66bb6a',      # Hijau
    'recovered':    '#29b6f6',      # Cyan cerah
}

st.markdown(f"""
<style>
    /* Main Background */
    .stApp {{
        background-color: {COLOR_SCHEME['dark_bg']};
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {COLOR_SCHEME['card_bg']};
    }}
    
    /* Metric Cards */
    .metric-card {{
        background: linear-gradient(135deg, {COLOR_SCHEME['card_bg']} 0%, {COLOR_SCHEME['card_bg']} 100%);
        border: 1px solid {COLOR_SCHEME['border']};
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }}
    
    /* Header Styling */
    h1, h2, h3, h4, h5, h6 {{
        color: {COLOR_SCHEME['text_light']} !important;
    }}
    
    /* Text */
    p, span, label, div {{
        color: {COLOR_SCHEME['text_light']} !important;
    }}
    
    /* Button */
    .stButton > button {{
        background-color: {COLOR_SCHEME['primary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 30px;
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: {COLOR_SCHEME['secondary']};
        box-shadow: 0 4px 15px rgba(255, 127, 14, 0.3);
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        color: {COLOR_SCHEME['text_light']} !important;
        background-color: {COLOR_SCHEME['card_bg']} !important;
    }}
    
    /* Slider */
    .stSlider > div > div > div > div {{
        background-color: {COLOR_SCHEME['primary']} !important;
    }}
    
    /* Checkbox */
    .stCheckbox > label {{
        color: {COLOR_SCHEME['text_light']} !important;
    }}
    
    /* Tabs */
    .stTabs > [data-baseweb="tab-list"] {{
        background-color: {COLOR_SCHEME['card_bg']};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {COLOR_SCHEME['text_light']};
        border-bottom: 2px solid transparent;
    }}
    
    .stTabs [aria-selected="true"] {{
        border-bottom-color: {COLOR_SCHEME['primary']} !important;
        color: {COLOR_SCHEME['primary']} !important;
    }}
    
    /* Dataframe */
    .dataframe {{
        background-color: {COLOR_SCHEME['card_bg']} !important;
        color: {COLOR_SCHEME['text_light']} !important;
    }}
    
    /* Number Input */
    .stNumberInput > div > div > input {{
        background-color: {COLOR_SCHEME['card_bg']} !important;
        color: {COLOR_SCHEME['text_light']} !important;
        border-color: {COLOR_SCHEME['border']} !important;
    }}
    
    /* Info/Warning/Error Boxes */
    .stAlert {{
        background-color: {COLOR_SCHEME['card_bg']};
        border: 1px solid {COLOR_SCHEME['border']};
    }}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ║  SIDEBAR - PARAMETER CONFIGURATION  ║
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown("""
<div style='padding: 15px; border-radius: 10px; border: 2px solid #1f77b4; margin-bottom: 20px;'>
    <h2 style='margin: 0; color: #1f77b4;'>⚙️ KONFIGURASI SIMULASI</h2>
</div>
""", unsafe_allow_html=True)

with st.sidebar.expander("🌐 JARINGAN", expanded=True):
    st.markdown("""
    <p style='font-size: 12px; color: #999;'>Konfigurasi topologi jaringan server</p>
    """, unsafe_allow_html=True)
    
    n_agents = st.slider(
        "Jumlah Server Node",
        min_value=10, max_value=200, value=50, step=10,
        help="Total node server dalam simulasi"
    )
    
    edge_prob = st.slider(
        "Probabilitas Koneksi",
        min_value=0.01, max_value=0.30, value=0.08, step=0.01,
        help="Probabilitas Erdős–Rényi Random Graph"
    )
    
    initial_infected = st.slider(
        "Node Terinfeksi Awal",
        min_value=1, max_value=20, value=5, step=1,
        help="Jumlah node yang terinfeksi di awal simulasi"
    )

with st.sidebar.expander("🔬 DINAMIKA PENYEBARAN", expanded=True):
    st.markdown("""
    <p style='font-size: 12px; color: #999;'>Parameter epidemiologis penyebaran</p>
    """, unsafe_allow_html=True)
    
    beta = st.slider(
        "Infection Rate (β)",
        min_value=0.10, max_value=0.80, value=0.30, step=0.05,
        help="Tingkat infeksi dari node yang terkena"
    )
    
    gamma = st.slider(
        "Recovery Rate (γ)",
        min_value=0.01, max_value=0.20, value=0.05, step=0.01,
        help="Tingkat pemulihan alami per langkah"
    )
    
    epsilon = st.slider(
        "Ancaman Eksternal (ε)",
        min_value=0.001, max_value=0.05, value=0.01, step=0.001,
        help="Probabilitas serangan eksternal acak"
    )

with st.sidebar.expander("🛠️ INTERVENSI", expanded=True):
    st.markdown("""
    <p style='font-size: 12px; color: #999;'>Strategi mitigasi keamanan</p>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        alpha = st.slider(
            "Efektivitas Patch (α)",
            min_value=0.20, max_value=1.00, value=0.60, step=0.05,
            help="Seberapa efektif patch mengurangi kerentanan"
        )
    
    with col2:
        tau = st.slider(
            "Efektivitas Training (τ)",
            min_value=0.20, max_value=1.00, value=0.50, step=0.05,
            help="Seberapa efektif training mengurangi risiko"
        )
    
    use_patch = st.checkbox(
        "Aktifkan Patch Management",
        value=False,
        help="Terapkan patch management untuk mengurangi kerentanan"
    )
    
    if use_patch:
        patch_proactive = st.checkbox(
            "   └─ Mode Proaktif (semua node)",
            value=False,
            help="Jika diaktifkan, patch diterapkan ke semua node susceptible"
        )
        patch_threshold = st.slider(
            "   └─ Ambang Kerentanan",
            min_value=0.30, max_value=1.00, value=0.70, step=0.05,
            help="Hanya patch node dengan kerentanan di atas threshold"
        )
    else:
        patch_proactive = False
        patch_threshold = 0.70

    use_training = st.checkbox(
        "Aktifkan User Training",
        value=False,
        help="Jalankan program pelatihan kesadaran keamanan"
    )
    
    if use_training:
        training_interval = st.slider(
            "   └─ Interval Training (steps)",
            min_value=5, max_value=50, value=10, step=5,
            help="Training dijalankan setiap N langkah"
        )
    else:
        training_interval = 10

with st.sidebar.expander("⏱️ EKSEKUSI", expanded=True):
    st.markdown("""
    <p style='font-size: 12px; color: #999;'>Pengaturan jalannya simulasi</p>
    """, unsafe_allow_html=True)
    
    n_steps = st.slider(
        "Durasi Simulasi (langkah)",
        min_value=50, max_value=500, value=200, step=50,
        help="Jumlah langkah waktu dalam satu simulasi"
    )
    
    n_runs = st.slider(
        "Monte Carlo Runs",
        min_value=1, max_value=30, value=5, step=1,
        help="Jumlah percobaan independen untuk robust statistics"
    )
    
    random_seed = st.number_input(
        "Random Seed",
        min_value=1, value=42, step=1,
        help="Seed untuk reproducibility"
    )

# ═══════════════════════════════════════════════════════════════════════════════
# ║  MAIN CONTENT  ║
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# ║  MAIN CONTENT  ║
# ═══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div style='padding: 30px; background: linear-gradient(135deg, #1f77b4 0%, #0a0e27 100%); 
            border-radius: 10px; margin-bottom: 30px; border: 2px solid #1f77b4;'>
    <h1 style='margin: 0; color: #fff; font-size: 2.5em;'>Cyber Threat Simulator</h1>
    <p style='margin: 5px 0 0 0; color: #ccc; font-size: 1.1em;'>
        Agent-Based Modeling untuk Simulasi Penyebaran Ancaman Siber dalam Jaringan
    </p>
</div>
""", unsafe_allow_html=True)

# Status dan Tombol Jalankan
col1, col2, col3 = st.columns([2, 2, 1.5])

with col3:
    run_button = st.button(
        "▶️ JALANKAN SIMULASI",
        key="run_sim",
        use_container_width=True,
        help="Mulai proses simulasi dengan parameter yang telah dikonfigurasi"
    )

# Persiapan model kwargs
model_kwargs = {
    'n_agents': n_agents,
    'initial_infected': initial_infected,
    'edge_prob': edge_prob,
    'beta': beta,
    'gamma': gamma,
    'epsilon': epsilon,
    'alpha': alpha,
    'tau': tau,
    'use_patch': use_patch,
    'use_training': use_training,
    'patch_proactive': patch_proactive,
    'training_interval': training_interval,
    'patch_threshold': patch_threshold,
}

# Jalankan simulasi jika tombol diklik
if run_button or 'simulation_results' in st.session_state:
    if run_button:
        st.session_state['running'] = True
    
    if st.session_state.get('running'):
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        status_placeholder.info("⏳ Simulasi sedang berjalan... Harap tunggu...")
        
        # Jalankan multiple runs
        all_results = []
        for run_id in range(n_runs):
            result = run_single_simulation(
                {**model_kwargs, 'seed': random_seed + run_id},
                n_steps,
                progress_placeholder
            )
            all_results.append(result)
            status_placeholder.info(f"⏳ Menyelesaikan run {run_id + 1}/{n_runs}...")
        
        st.session_state['simulation_results'] = all_results
        status_placeholder.success("✅ Simulasi selesai!")
        progress_placeholder.empty()

# Tampilkan hasil jika ada
if 'simulation_results' in st.session_state and st.session_state['simulation_results']:
    results = st.session_state['simulation_results']
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ║  RINGKASAN STATISTIK  ║
    # ═══════════════════════════════════════════════════════════════════════════
    
    st.markdown("""
    <div style='margin: 30px 0 20px 0;'>
        <h2 style='color: #e8eaed; font-size: 1.8em; margin: 0;'>Ringkasan Hasil Simulasi</h2>
        <p style='color: #999; font-size: 0.95em; margin: 5px 0 0 0;'>Statistik agregat dari semua Monte Carlo runs</p>
    </div>
    """, unsafe_allow_html=True)
    
    peak_infected_vals = [r['peak_infected'] for r in results]
    recovery_steps = [r['recovery_step'] for r in results]
    vulnerabilities = [r['vulnerability_akhir'] for r in results]
    awareness = [r['user_awareness_akhir'] for r in results]
    
    col1, col2, col3, col4 = st.columns(4, gap="large")
    
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #ff5252 0%, rgba(255, 82, 82, 0.2) 100%);
                    border-left: 4px solid #ff5252; border-radius: 8px; padding: 20px;'>
            <div style='font-size: 0.85em; color: #ff5252; font-weight: 600; margin-bottom: 10px;'>PUNCAK INFEKSI</div>
            <div style='font-size: 2em; color: #fff; font-weight: bold; margin-bottom: 5px;'>{np.mean(peak_infected_vals):.1f}</div>
            <div style='font-size: 0.9em; color: #ccc;'>{np.mean(peak_infected_vals)/n_agents*100:.1f}% dari {n_agents} node</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #66bb6a 0%, rgba(102, 187, 106, 0.2) 100%);
                    border-left: 4px solid #66bb6a; border-radius: 8px; padding: 20px;'>
            <div style='font-size: 0.85em; color: #66bb6a; font-weight: 600; margin-bottom: 10px;'>PEMULIHAN</div>
            <div style='font-size: 2em; color: #fff; font-weight: bold; margin-bottom: 5px;'>{np.mean(recovery_steps):.0f}</div>
            <div style='font-size: 0.9em; color: #ccc;'>Langkah hingga pemulihan</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #ffa726 0%, rgba(255, 167, 38, 0.2) 100%);
                    border-left: 4px solid #ffa726; border-radius: 8px; padding: 20px;'>
            <div style='font-size: 0.85em; color: #ffa726; font-weight: 600; margin-bottom: 10px;'>KERENTANAN AKHIR</div>
            <div style='font-size: 2em; color: #fff; font-weight: bold; margin-bottom: 5px;'>{np.mean(vulnerabilities):.4f}</div>
            <div style='font-size: 0.9em; color: #ccc;'>Rata-rata semua node</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #29b6f6 0%, rgba(41, 182, 246, 0.2) 100%);
                    border-left: 4px solid #29b6f6; border-radius: 8px; padding: 20px;'>
            <div style='font-size: 0.85em; color: #29b6f6; font-weight: 600; margin-bottom: 10px;'>KESADARAN AKHIR</div>
            <div style='font-size: 2em; color: #fff; font-weight: bold; margin-bottom: 5px;'>{np.mean(awareness):.4f}</div>
            <div style='font-size: 0.9em; color: #ccc;'>Rata-rata semua node</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ║  TABS UNTUK BERBAGAI VISUALISASI  ║
    # ═══════════════════════════════════════════════════════════════════════════
    
    st.markdown("""
    <div style='margin: 40px 0 20px 0;'>
        <h2 style='color: #e8eaed; font-size: 1.8em; margin: 0;'>Visualisasi & Analisis</h2>
        <p style='color: #999; font-size: 0.95em; margin: 5px 0 0 0;'>Eksplorasi hasil simulasi melalui berbagai perspektif</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📉 Time-Series",
        "📊 Distribusi",
        "🔗 Topologi Jaringan",
        "🌡️ Heatmap Kerentanan",
        "📋 Data Raw"
    ])
    
    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: TIME-SERIES
    # ─────────────────────────────────────────────────────────────────────────
    
    with tab1:
        st.markdown("""
        <div style='background: #141829; border-left: 4px solid #1f77b4; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
            <p style='margin: 0; color: #e8eaed;'><b>Dinamika Infeksi & Kerentanan</b></p>
            <p style='margin: 5px 0 0 0; font-size: 0.9em; color: #999;'>Grafik menunjukkan perkembangan infeksi dan tingkat kerentanan sepanjang waktu simulasi</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Gabungkan data dari semua runs
        combined_data = pd.concat([r['data'] for r in results], ignore_index=True)
        
        col_ts1, col_ts2 = st.columns(2)
        
        with col_ts1:
            # Time-series infected
            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor('#0a0e27')
            ax.set_facecolor('#141829')
            
            for run_id, result in enumerate(results):
                ax.plot(result['data']['langkah'], result['data']['n_infected'], 
                       alpha=0.25, color='#666', linewidth=0.8)
            
            # Plot rata-rata
            avg_infected = combined_data.groupby('langkah')['n_infected'].mean()
            ax.plot(avg_infected.index, avg_infected.values, color='#ff5252', 
                   linewidth=3, label='Rata-rata', zorder=5)
            
            ax.set_xlabel('Langkah Waktu', color='#e8eaed', fontsize=11)
            ax.set_ylabel('Jumlah Node Terinfeksi', color='#e8eaed', fontsize=11)
            ax.set_title('Dinamika Infeksi', color='#e8eaed', fontweight='bold', fontsize=12)
            ax.legend(loc='best', facecolor='#141829', edgecolor='#2d3142', labelcolor='#e8eaed')
            ax.grid(True, alpha=0.2, color='#2d3142')
            ax.tick_params(colors='#e8eaed')
            
            st.pyplot(fig)
        
        with col_ts2:
            # Time-series vulnerability
            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor('#0a0e27')
            ax.set_facecolor('#141829')
            
            for run_id, result in enumerate(results):
                ax.plot(result['data']['langkah'], result['data']['rata_vulnerability'], 
                       alpha=0.25, color='#666', linewidth=0.8)
            
            # Plot rata-rata
            avg_vuln = combined_data.groupby('langkah')['rata_vulnerability'].mean()
            ax.plot(avg_vuln.index, avg_vuln.values, color='#ffa726', 
                   linewidth=3, label='Rata-rata', zorder=5)
            
            ax.set_xlabel('Langkah Waktu', color='#e8eaed', fontsize=11)
            ax.set_ylabel('Rata-rata Tingkat Kerentanan', color='#e8eaed', fontsize=11)
            ax.set_title('Evolusi Kerentanan', color='#e8eaed', fontweight='bold', fontsize=12)
            ax.legend(loc='best', facecolor='#141829', edgecolor='#2d3142', labelcolor='#e8eaed')
            ax.grid(True, alpha=0.2, color='#2d3142')
            ax.tick_params(colors='#e8eaed')
            
            st.pyplot(fig)
    
    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: DISTRIBUSI
    # ─────────────────────────────────────────────────────────────────────────
    
    with tab2:
        st.markdown("""
        <div style='background: #141829; border-left: 4px solid #2ca02c; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
            <p style='margin: 0; color: #e8eaed;'><b>Distribusi Puncak Infeksi</b></p>
            <p style='margin: 5px 0 0 0; font-size: 0.9em; color: #999;'>Histogram menunjukkan sebaran puncak node terinfeksi dari semua Monte Carlo runs</p>
        </div>
        """, unsafe_allow_html=True)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#0a0e27')
        ax.set_facecolor('#141829')
        
        ax.hist(peak_infected_vals, bins=15, color='#ff5252', alpha=0.7, 
               edgecolor='#ff7676', linewidth=1.5)
        ax.axvline(np.mean(peak_infected_vals), color='#66bb6a', linestyle='--', 
                  linewidth=2.5, label=f"Mean: {np.mean(peak_infected_vals):.1f}")
        ax.axvline(np.median(peak_infected_vals), color='#29b6f6', linestyle=':', 
                  linewidth=2.5, label=f"Median: {np.median(peak_infected_vals):.1f}")
        
        ax.set_xlabel('Puncak Node Terinfeksi', color='#e8eaed', fontsize=11)
        ax.set_ylabel('Frekuensi', color='#e8eaed', fontsize=11)
        ax.set_title(f'Distribusi Puncak Infeksi ({n_runs} Monte Carlo Runs)', 
                    color='#e8eaed', fontweight='bold', fontsize=12)
        ax.legend(facecolor='#141829', edgecolor='#2d3142', labelcolor='#e8eaed', loc='best')
        ax.grid(True, alpha=0.2, axis='y', color='#2d3142')
        ax.tick_params(colors='#e8eaed')
        
        st.pyplot(fig)
    
    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: TOPOLOGI JARINGAN
    # ─────────────────────────────────────────────────────────────────────────
    
    with tab3:
        st.markdown("""
        <div style='background: #141829; border-left: 4px solid #17a2b8; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
            <p style='margin: 0; color: #e8eaed;'><b>Snapshot Topologi Jaringan</b></p>
            <p style='margin: 5px 0 0 0; font-size: 0.9em; color: #999;'>Visualisasi evolusi state node pada 4 titik waktu (Run pertama)</p>
        </div>
        """, unsafe_allow_html=True)
        
        if results:
            graph = results[0]['graph']
            model = results[0]['model']
            
            # Ambil snapshot dari berbagai langkah
            steps_to_show = [0, n_steps // 3, 2 * n_steps // 3, n_steps - 1]
            
            fig, axes = plt.subplots(1, 4, figsize=(18, 4))
            fig.patch.set_facecolor('#0a0e27')
            
            pos = nx.spring_layout(graph, seed=42, k=1.2)
            
            for idx, ax in enumerate(axes):
                ax.set_facecolor('#141829')
                
                # Ambil state dari data run pertama
                step_data = results[0]['data'].iloc[idx * (len(results[0]['data']) // 4)]
                
                # Generate colors - minimal distribution untuk menghindari overlap
                node_colors_list = [
                    STATE_COLORS_MAP['susceptible'],    # Biru
                    STATE_COLORS_MAP['infected'],       # Merah
                    STATE_COLORS_MAP['patched'],        # Hijau
                    STATE_COLORS_MAP['recovered']       # Cyan
                ]
                node_colors = [node_colors_list[i % 4] for i in range(len(graph.nodes))]
                
                nx.draw_networkx(
                    graph, pos=pos, ax=ax,
                    node_color=node_colors, node_size=120,
                    edge_color='#2d3142', with_labels=False, alpha=0.85, width=0.6
                )
                ax.set_title(f"Langkah {int(idx * n_steps / 4)}", 
                            color='#e8eaed', fontweight='bold', fontsize=11)
                ax.axis('off')
            
            st.pyplot(fig)
    
    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4: HEATMAP
    # ─────────────────────────────────────────────────────────────────────────
    
    with tab4:
        st.markdown("""
        <div style='background: #141829; border-left: 4px solid #ffa726; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
            <p style='margin: 0; color: #e8eaed;'><b>Evolusi Kerentanan per Run</b></p>
            <p style='margin: 5px 0 0 0; font-size: 0.9em; color: #999;'>Heatmap menunjukkan perubahan tingkat kerentanan sepanjang waktu untuk setiap run</p>
        </div>
        """, unsafe_allow_html=True)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        fig.patch.set_facecolor('#0a0e27')
        
        # Buat heatmap dari vulnerability semua runs
        vulnerability_matrix = np.array([r['data']['rata_vulnerability'].values for r in results])
        
        im = ax.imshow(vulnerability_matrix, cmap='YlOrRd', aspect='auto', interpolation='bilinear')
        ax.set_xlabel('Langkah Waktu', color='#e8eaed', fontsize=11)
        ax.set_ylabel('Run ID', color='#e8eaed', fontsize=11)
        ax.set_title('Heatmap Evolusi Kerentanan', color='#e8eaed', fontweight='bold', fontsize=12)
        
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Tingkat Kerentanan', color='#e8eaed', fontsize=11)
        cbar.ax.tick_params(colors='#e8eaed')
        
        ax.tick_params(colors='#e8eaed')
        
        st.pyplot(fig)
    
    # ─────────────────────────────────────────────────────────────────────────
    # TAB 5: DATA RAW
    # ─────────────────────────────────────────────────────────────────────────
    
    with tab5:
        st.markdown("""
        <div style='background: #141829; border-left: 4px solid #1f77b4; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
            <p style='margin: 0; color: #e8eaed;'><b>Data Raw Simulasi</b></p>
            <p style='margin: 5px 0 0 0; font-size: 0.9em; color: #999;'>Tabel berisi data mentah lengkap dari semua run dan setiap langkah simulasi</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tambahkan run_id ke combined data
        combined_with_run = []
        for run_id, result in enumerate(results):
            df = result['data'].copy()
            df['run_id'] = run_id + 1
            combined_with_run.append(df)
        
        combined_df = pd.concat(combined_with_run, ignore_index=True)
        
        # Reorder columns
        cols = ['run_id', 'langkah', 'n_susceptible', 'n_infected', 'n_patched', 
                'n_recovered', 'rata_vulnerability', 'rata_user_awareness']
        combined_df = combined_df[cols]
        
        st.dataframe(combined_df, use_container_width=True, height=400)
        
        st.markdown("---")
        
        col_d1, col_d2, col_d3 = st.columns([1, 1, 2])
        
        with col_d1:
            csv = combined_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"cyber_threat_sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_d2:
            # Summary statistics
            st.markdown("""
            <div style='background: #141829; border-left: 4px solid #2ca02c; padding: 15px; border-radius: 5px;'>
                <p style='margin: 0; color: #e8eaed; font-weight: bold;'>Ringkasan Data</p>
                <p style='margin: 5px 0 0 0; font-size: 0.9em; color: #999;'>
                    Total Baris: <span style='color: #29b6f6;'>{}</span><br>
                    Total Runs: <span style='color: #29b6f6;'>{}</span><br>
                    Langkah per Run: <span style='color: #29b6f6;'>{}</span>
                </p>
            </div>
            """.format(len(combined_df), n_runs, n_steps), unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em; padding: 20px;'>
    <p style='margin: 5px 0;'>Cyber Threat Simulator Dashboard</p>
    <p style='margin: 5px 0;'>Agent-Based Modeling dengan Mesa Framework</p>
    <p style='margin: 10px 0 0 0; font-size: 0.85em; color: #555;'>Tugas Akhir - Semester 6</p>
</div>
""", unsafe_allow_html=True)
