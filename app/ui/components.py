"""Componentes reutilizables — tema claro estilo Bremen."""
import html as _html
import streamlit as st
from app.utils.formatters import fmt_moneda, fmt_pct
from app.services.precio_service import DesglosePrecio

GLOBAL_CSS = """
<style>
/* ── Base ────────────────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background: #F4F5F7 !important; }
[data-testid="stHeader"]           { background: #FFFFFF !important;
                                     border-bottom: 1px solid #E4E6EB; }
section[data-testid="stMain"] > div { padding-top: 0.5rem; }
[data-testid="stMainBlockContainer"] { max-width: 1200px; }

/* ── Tabs ────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 0 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    margin-bottom: 16px;
}
[data-testid="stTabs"] button {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #8A8FA8 !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 16px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #FF6B35 !important;
    border-bottom: 2px solid #FF6B35 !important;
}

/* ── Inputs ──────────────────────────────────────────────────────────── */
input, textarea {
    background: #FFFFFF !important;
    border: 1.5px solid #DDE0E8 !important;
    border-radius: 8px !important;
    color: #1A1D2E !important;
    font-size: 0.92rem !important;
}
input:focus { border-color: #FF6B35 !important;
              box-shadow: 0 0 0 3px rgba(255,107,53,.12) !important; }

/* ── Selectbox ───────────────────────────────────────────────────────── */
[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1.5px solid #DDE0E8 !important;
    border-radius: 8px !important;
}

/* ── Botones ─────────────────────────────────────────────────────────── */
[data-testid="baseButton-primary"] {
    background: #FF6B35 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    letter-spacing: 0.2px !important;
    box-shadow: 0 2px 8px rgba(255,107,53,.3) !important;
}
[data-testid="baseButton-secondary"] {
    background: #FFFFFF !important;
    border: 1.5px solid #DDE0E8 !important;
    border-radius: 8px !important;
    color: #5A6080 !important;
}

/* ── Dataframe ───────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #E4E6EB !important;
    border-radius: 10px !important;
    overflow: hidden;
    background: #FFFFFF;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}

/* ── Tarjeta de producto (estilo Bremen) ─────────────────────────────── */
.product-card {
    background: #FFFFFF;
    border: 1px solid #E4E6EB;
    border-radius: 10px;
    padding: 0;
    margin-bottom: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
    overflow: hidden;
}
.product-card-header {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
    gap: 0;
    padding: 16px 20px;
    align-items: center;
}
.product-col-label {
    font-size: 0.68rem;
    font-weight: 700;
    color: #A0A8C0;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 3px;
}
.product-description {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1A1D2E;
    line-height: 1.3;
}
.product-code {
    font-size: 0.82rem;
    color: #8A8FA8;
    margin-top: 2px;
}
.product-price {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1A1D2E;
}
.product-price-venta {
    font-size: 1.7rem;
    font-weight: 800;
    color: #1E9E55;
    line-height: 1.1;
}
.product-empaque {
    display: inline-block;
    background: #FF6B35;
    color: #FFFFFF;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 1rem;
    font-weight: 800;
    letter-spacing: 0.5px;
}
.product-ganancia {
    font-size: 0.9rem;
    font-weight: 700;
    color: #E74C3C;
    margin-top: 6px;
}

/* ── Desglose expandido ──────────────────────────────────────────────── */
.breakdown-bar {
    background: #F8F9FB;
    border-top: 1px solid #E4E6EB;
    padding: 16px 20px;
}
.flow-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.flow-step {
    background: #FFFFFF;
    border: 1px solid #E4E6EB;
    border-radius: 8px;
    padding: 8px 14px;
    text-align: center;
    min-width: 96px;
}
.flow-step-label { font-size: 0.62rem; color: #A0A8C0; text-transform: uppercase; letter-spacing: 0.8px; }
.flow-step-value { font-size: 0.9rem; font-weight: 700; color: #1A1D2E; }
.flow-step-value.verde { color: #1E9E55; }
.flow-arrow { color: #C8CEDD; font-size: 1rem; }
.flow-op    { font-size: 0.68rem; color: #A0A8C0; text-align: center; }

/* ── Tabla-header Bremen ─────────────────────────────────────────────── */
.bremtable-header {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
    padding: 8px 20px;
    font-size: 0.72rem;
    font-weight: 700;
    color: #A0A8C0;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 1px solid #E4E6EB;
    background: #FFFFFF;
    border-radius: 10px 10px 0 0;
    margin-bottom: 0;
}

/* ── Stats ───────────────────────────────────────────────────────────── */
.stat-card {
    background: #FFFFFF;
    border: 1px solid #E4E6EB;
    border-radius: 10px;
    padding: 18px 16px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
.stat-num   { font-size: 1.9rem; font-weight: 800; color: #FF6B35; }
.stat-label { font-size: 0.78rem; color: #8A8FA8; margin-top: 4px; }

/* ── Notificaciones ──────────────────────────────────────────────────── */
.notif-ok   { background:#EBF9F1; border-left:3px solid #1E9E55; padding:9px 14px; border-radius:6px; margin:6px 0; font-size:0.87rem; color:#1A5C34; }
.notif-err  { background:#FDF0EE; border-left:3px solid #E74C3C; padding:9px 14px; border-radius:6px; margin:6px 0; font-size:0.87rem; color:#7B1A14; }
.notif-warn { background:#FEF9EC; border-left:3px solid #F39C12; padding:9px 14px; border-radius:6px; margin:6px 0; font-size:0.87rem; color:#7B5A00; }

/* ── Sección título ──────────────────────────────────────────────────── */
.seccion-titulo {
    font-size: 0.68rem;
    font-weight: 700;
    color: #A0A8C0;
    text-transform: uppercase;
    letter-spacing: 2px;
    padding-bottom: 8px;
    border-bottom: 1px solid #E4E6EB;
    margin: 20px 0 14px;
}

/* ── Expander limpio ─────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #E4E6EB !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.04) !important;
}
</style>
"""


def inject_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def _deindent(html: str) -> str:
    """Elimina sangría de cada línea para evitar que Markdown interprete el HTML como bloque de código."""
    return "\n".join(line.lstrip() for line in html.splitlines())


# ── Notificaciones ────────────────────────────────────────────────────────────
def notif_ok(msg: str)   -> None: st.markdown(f'<div class="notif-ok">✓ {msg}</div>',   unsafe_allow_html=True)
def notif_err(msg: str)  -> None: st.markdown(f'<div class="notif-err">✕ {msg}</div>',  unsafe_allow_html=True)
def notif_warn(msg: str) -> None: st.markdown(f'<div class="notif-warn">⚠ {msg}</div>', unsafe_allow_html=True)


# ── Tarjeta estilo Bremen ─────────────────────────────────────────────────────

def tarjeta_precio(
    descripcion: str,
    empaque: str | None,
    proveedor: str,
    desglose: DesglosePrecio,
    codigo: str | None = None,
) -> None:
    desc_s     = _html.escape(str(descripcion or ""))
    prov_s     = _html.escape(str(proveedor or ""))
    empaque_label = _html.escape(empaque.strip() if empaque and empaque.strip() else "Empaque no espec.")
    codigo_s   = _html.escape(str(codigo)) if codigo else None
    descuento_monto = desglose.precio_lista - desglose.costo_real
    iva_monto       = desglose.costo_con_iva - desglose.costo_real

    st.markdown(_deindent(f"""
    <div class="product-card">

      <div class="product-card-header">

        <div>
          <div class="product-description">{desc_s}</div>
          <div class="product-code">
            {'<span style="margin-right:10px">' + codigo_s + '</span>' if codigo_s else ''}
            🏭 {prov_s}
          </div>
        </div>

        <div>
          <div class="product-col-label">Lista</div>
          <div class="product-price">{fmt_moneda(desglose.precio_lista)}</div>
        </div>

        <div>
          <div class="product-col-label">Costo + IVA</div>
          <div class="product-price">{fmt_moneda(desglose.costo_con_iva)}</div>
        </div>

        <div style="background:#EBF9F1;border:2px solid #1E9E55;border-radius:10px;padding:10px 14px">
          <div class="product-col-label" style="color:#1E9E55">Precio Venta</div>
          <div class="product-price-venta">{fmt_moneda(desglose.precio_venta)}</div>
        </div>

        <div>
          <div class="product-col-label">Empaque</div>
          <span class="product-empaque">{empaque_label}</span>
          <div class="product-ganancia" style="margin-top:6px">
            {fmt_moneda(desglose.ganancia_neta)} · {fmt_pct(desglose.ganancia_neta_pct)}
          </div>
        </div>

      </div>

      <div class="breakdown-bar">
        <div class="flow-wrap">
          <div class="flow-step">
            <div class="flow-step-label">Lista</div>
            <div class="flow-step-value">{fmt_moneda(desglose.precio_lista)}</div>
          </div>
          <div>
            <div class="flow-arrow">&#8594;</div>
            <div class="flow-op">&#8722;{fmt_pct(desglose.descuento_pct)}<br>{fmt_moneda(-descuento_monto)}</div>
          </div>
          <div class="flow-step">
            <div class="flow-step-label">Costo real</div>
            <div class="flow-step-value">{fmt_moneda(desglose.costo_real)}</div>
          </div>
          <div>
            <div class="flow-arrow">&#8594;</div>
            <div class="flow-op">+IVA {fmt_pct(desglose.iva_pct)}<br>+{fmt_moneda(iva_monto)}</div>
          </div>
          <div class="flow-step">
            <div class="flow-step-label">Costo + IVA</div>
            <div class="flow-step-value">{fmt_moneda(desglose.costo_con_iva)}</div>
          </div>
          <div>
            <div class="flow-arrow">&#8594;</div>
            <div class="flow-op">+{fmt_pct(desglose.ganancia_pct)}<br>+{fmt_moneda(desglose.ganancia_neta)}</div>
          </div>
          <div class="flow-step" style="border-color:#1E9E55;border-width:2px;background:#EBF9F1">
            <div class="flow-step-label" style="color:#1E9E55">Precio Venta</div>
            <div class="flow-step-value verde" style="font-size:1.15rem">{fmt_moneda(desglose.precio_venta)}</div>
          </div>
        </div>
      </div>

    </div>
    """), unsafe_allow_html=True)


# ── Stat card ─────────────────────────────────────────────────────────────────
def stat_card(numero: str, label: str) -> None:
    st.markdown(
        f'<div class="stat-card"><div class="stat-num">{numero}</div>'
        f'<div class="stat-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


# ── Sección ───────────────────────────────────────────────────────────────────
def seccion(titulo: str) -> None:
    st.markdown(f'<div class="seccion-titulo">{titulo}</div>', unsafe_allow_html=True)
