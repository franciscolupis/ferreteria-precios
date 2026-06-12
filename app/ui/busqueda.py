import streamlit as st
import pandas as pd
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

    # ── Encabezado de tabla (estilo Bremen) ───────────────────────────────────
    st.markdown(
        '<div class="bremtable-header">'
        "<span>Descripción</span>"
        "<span>Precio Lista</span>"
        "<span>Costo + IVA</span>"
        "<span>Precio Venta</span>"
        "<span>Empaque / Ganancia</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Tabla de resultados con selección ─────────────────────────────────────
    df = pd.DataFrame([
        {
            "Código":        r.get("codigo_producto") or "",
            "Descripción":   r["descripcion"],
            "Proveedor":     r["proveedor"],
            "Precio lista":  r["precio_lista"],
            "_id":           r["id"],
        }
        for r in resultados
    ])

    evento = st.dataframe(
        df[["Código", "Descripción", "Proveedor", "Precio lista"]],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Precio lista": st.column_config.NumberColumn(format="$ %,.2f"),
        },
    )

    # ── Detalle del producto seleccionado ─────────────────────────────────────
    filas_sel = evento.selection.get("rows", []) if hasattr(evento, "selection") else []
    if not filas_sel:
        return

    idx = filas_sel[0]
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
