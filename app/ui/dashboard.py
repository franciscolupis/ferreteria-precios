import streamlit as st
from app.services import producto_service
from app.ui.components import stat_card, seccion, notif_err
from app.utils.formatters import fmt_moneda


def render() -> None:
    seccion("Panel de Control")

    try:
        stats = producto_service.stats_generales()
    except Exception as exc:
        notif_err(f"Error al cargar estadísticas: {exc}")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        stat_card(str(stats["total_productos"]), "Productos cargados")
    with col2:
        stat_card(str(stats["total_proveedores"]), "Proveedores")
    with col3:
        stat_card(fmt_moneda(stats["precio_promedio"]), "Precio lista promedio")
    with col4:
        ultima = stats["ultima_actualizacion"]
        if ultima:
            ultima = str(ultima)[:10]
        else:
            ultima = "—"
        stat_card(ultima, "Última actualización")
