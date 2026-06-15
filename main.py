import base64
from pathlib import Path
import streamlit as st
from app.utils.logger import setup_logging
from app.database.connection import init_db
from app.ui.components import inject_css
from app.ui import busqueda, dashboard, proveedores, reglas, importar


def _logo_b64() -> str:
    logo = Path(__file__).parent / "assets" / "logo.png"
    return base64.b64encode(logo.read_bytes()).decode()

setup_logging()
init_db()

st.set_page_config(
    page_title="Ferretería — Precios",
    page_icon="🔩",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()

# ── Header con logo ───────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#1A1D2E; border-bottom:3px solid #E8A020;
            border-radius:8px; padding:10px 24px; margin-bottom:16px;">
""", unsafe_allow_html=True)
st.image(str(Path(__file__).parent / "assets" / "logo.png"), width=280)
st.markdown("</div>", unsafe_allow_html=True)

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
