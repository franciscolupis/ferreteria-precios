import streamlit as st
from app.utils.logger import setup_logging
from app.database.connection import init_db
from app.ui.components import inject_css
from app.ui import busqueda, dashboard, proveedores, reglas, importar

setup_logging()
init_db()

st.set_page_config(
    page_title="Ferretería — Precios",
    page_icon="🔩",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()

# ── Header estilo Bremen ──────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Barra superior fija estilo Bremen */
  .bremen-topbar {
    display: flex;
    align-items: center;
    gap: 0;
    background: #FFFFFF;
    border-bottom: 1px solid #E4E6EB;
    padding: 10px 24px;
    margin: -0.5rem -1rem 20px;
    position: sticky;
    top: 0;
    z-index: 99;
  }
  .bremen-logo {
    width: 36px; height: 36px;
    background: linear-gradient(135deg,#FF6B35,#C04A1A);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; font-weight: 900; color: white;
    margin-right: 20px; flex-shrink: 0;
  }
  .bremen-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #1A1D2E;
    margin-right: auto;
  }
</style>
<div class="bremen-topbar">
  <div class="bremen-logo">🔩</div>
  <div class="bremen-title">Productos</div>
  <div style="font-size:0.8rem; color:#8A8FA8">Gestión de Precios</div>
</div>
""", unsafe_allow_html=True)

# ── Buscador full-width estilo Bremen ─────────────────────────────────────────
st.markdown("""
<style>
  /* hace el input más parecido al search de Bremen */
  [data-testid="stTextInput"] > div > div > input {
    height: 44px !important;
    font-size: 0.95rem !important;
    padding-left: 16px !important;
  }
</style>
""", unsafe_allow_html=True)

st.text_input(
    label="busqueda",
    placeholder="🔍  Ingrese el valor a buscar...",
    label_visibility="collapsed",
    key="busqueda_global",
)

st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_b, tab_d, tab_p, tab_r, tab_i = st.tabs([
    "Productos",
    "Dashboard",
    "Proveedores",
    "Reglas Financieras",
    "Importar Lista",
])

with tab_b:  busqueda.render()
with tab_d:  dashboard.render()
with tab_p:  proveedores.render()
with tab_r:  reglas.render()
with tab_i:  importar.render()
