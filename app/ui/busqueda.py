import streamlit as st
from app.services import producto_service, precio_service, exportador, proveedor_service
from app.ui.components import tarjeta_precio, notif_err, notif_warn, seccion
from app.utils.formatters import fmt_moneda


def render() -> None:
    termino = st.session_state.get("busqueda_global", "")

    # ── Filtro por proveedor (estilo Bremen: filtro junto al buscador) ────────
    try:
        provs = proveedor_service.listar()
    except Exception:
        provs = []

    opciones_prov = {"Todos los proveedores": None}
    opciones_prov.update({p["nombre"]: p["id"] for p in provs})

    col_fil, col_info = st.columns([2, 3])
    with col_fil:
        prov_sel = st.selectbox(
            "Proveedor",
            list(opciones_prov.keys()),
            label_visibility="collapsed",
            key="filtro_proveedor",
        )
    with col_info:
        if termino and len(termino) >= 2:
            st.markdown(
                f'<p style="color:#A0A8C0; font-size:0.8rem; padding-top:10px">'
                f'Buscando <b>"{termino}"</b>'
                f'{" en " + prov_sel if prov_sel != "Todos los proveedores" else ""}'
                f' — hacé clic en una fila para ver el precio detallado</p>',
                unsafe_allow_html=True,
            )

    prov_id_filtro = opciones_prov[prov_sel]

    if not termino or len(termino) < 2:
        st.markdown(
            '<div style="text-align:center; padding:60px 20px">'
            '<div style="font-size:2rem; margin-bottom:12px">🔍</div>'
            '<p style="color:#A0A8C0; font-size:0.95rem">Ingresá al menos 2 caracteres para buscar.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Buscar ────────────────────────────────────────────────────────────────
    try:
        resultados = producto_service.buscar(termino, prov_id_filtro)
    except Exception as exc:
        notif_err(f"Error al buscar: {exc}")
        return

    if not resultados:
        notif_warn(f'Sin resultados para "{termino}".')
        return

    # ── CSS para filas clicables ──────────────────────────────────────────────
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        text-align: left !important;
        padding: 10px 6px !important;
        font-size: 0.97rem !important;
        color: #1A1D2E !important;
        box-shadow: none !important;
        border-bottom: 1px solid #F0F1F5 !important;
    }
    div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
        background: #FFF3EE !important;
        color: #FF6B35 !important;
    }
    div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background: #FFF3EE !important;
        border: none !important;
        border-left: 3px solid #FF6B35 !important;
        border-radius: 0 !important;
        text-align: left !important;
        padding: 10px 6px !important;
        font-size: 0.97rem !important;
        color: #FF6B35 !important;
        box-shadow: none !important;
        border-bottom: 1px solid #F0F1F5 !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="column"]:last-child button[kind="secondary"] {
        color: #1E9E55 !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="column"]:last-child button[kind="primary"] {
        color: #1E9E55 !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Encabezado de tabla ───────────────────────────────────────────────────
    h1, h2, h3, h4 = st.columns([4, 2, 1.5, 1.5])
    hdr = '<span style="font-size:0.78rem;font-weight:700;color:#6B7399;text-transform:uppercase">{}</span>'
    h1.markdown(hdr.format("Descripción"), unsafe_allow_html=True)
    h2.markdown(hdr.format("Proveedor"), unsafe_allow_html=True)
    h3.markdown(hdr.format("Código"), unsafe_allow_html=True)
    h4.markdown('<span style="font-size:0.78rem;font-weight:700;color:#1E9E55;text-transform:uppercase">Precio Venta</span>', unsafe_allow_html=True)
    st.markdown('<div style="border-bottom:2px solid #E4E6EB;margin:2px 0 4px"></div>', unsafe_allow_html=True)

    # ── Filas clicables ───────────────────────────────────────────────────────
    sel_idx = st.session_state.get("prod_sel_idx")

    for i, r in enumerate(resultados):
        es_sel = (sel_idx == i)
        tipo   = "primary" if es_sel else "secondary"

        if r["descuento_pct"] is not None:
            d = precio_service.calcular(r["precio_lista"], r["descuento_pct"], r["iva_pct"], r["ganancia_pct"])
            precio_col = fmt_moneda(d.precio_venta)
        else:
            precio_col = "Sin reglas"

        c1, c2, c3, c4 = st.columns([4, 2, 1.5, 1.5])
        cl1 = c1.button(r["descripcion"],                     key=f"r{i}a", use_container_width=True, type=tipo)
        cl2 = c2.button(r["proveedor"],                       key=f"r{i}b", use_container_width=True, type=tipo)
        cl3 = c3.button(r.get("codigo_producto") or "—",     key=f"r{i}c", use_container_width=True, type=tipo)
        cl4 = c4.button(precio_col,                           key=f"r{i}d", use_container_width=True, type=tipo)
        if cl1 or cl2 or cl3 or cl4:
            st.session_state["prod_sel_idx"] = i
            st.rerun()

    # ── Detalle del producto seleccionado ─────────────────────────────────────
    if sel_idx is None or sel_idx >= len(resultados):
        return

    idx = sel_idx
    r   = resultados[idx]

    if r["descuento_pct"] is None:
        notif_warn(
            f"El proveedor «{r['proveedor']}» no tiene reglas financieras. "
            "Configuralo en la pestaña Reglas."
        )
        return

    desglose = precio_service.calcular(
        precio_lista=r["precio_lista"],
        descuento_pct=r["descuento_pct"],
        iva_pct=r["iva_pct"],
        ganancia_pct=r["ganancia_pct"],
    )

    st.markdown("<br>", unsafe_allow_html=True)

    tarjeta_precio(
        descripcion=r["descripcion"],
        empaque=r.get("empaque"),
        proveedor=r["proveedor"],
        desglose=desglose,
        codigo=r.get("codigo_producto"),
    )

    # ── Exportar ──────────────────────────────────────────────────────────────
    fila_export = {
        **r,
        "costo_real":        desglose.costo_real,
        "costo_con_iva":     desglose.costo_con_iva,
        "precio_venta":      desglose.precio_venta,
        "ganancia_neta":     desglose.ganancia_neta,
        "ganancia_neta_pct": desglose.ganancia_neta_pct,
    }

    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        try:
            pdf_bytes = exportador.exportar_pdf([fila_export], titulo=r["descripcion"])
            st.download_button(
                "⬇ PDF", data=pdf_bytes,
                file_name=f"{r['descripcion'][:35]}.pdf",
                mime="application/pdf", use_container_width=True,
            )
        except ImportError:
            pass
    with col2:
        try:
            xls_bytes = exportador.exportar_excel([fila_export], titulo=r["descripcion"])
            st.download_button(
                "⬇ Excel", data=xls_bytes,
                file_name=f"{r['descripcion'][:35]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except ImportError:
            pass
