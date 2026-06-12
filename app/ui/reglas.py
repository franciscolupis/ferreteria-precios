import streamlit as st
from app.services import proveedor_service
from app.services.precio_service import calcular
from app.ui.components import notif_ok, notif_err, notif_warn, seccion
from app.utils.formatters import fmt_moneda, fmt_pct


def render() -> None:
    seccion("Reglas Financieras")

    try:
        proveedores = proveedor_service.listar()
    except Exception as exc:
        notif_err(f"Error al cargar proveedores: {exc}")
        return

    if not proveedores:
        notif_warn("Primero crea al menos un proveedor.")
        return

    nombres = {p["nombre"]: p["id"] for p in proveedores}
    seleccion = st.selectbox("Seleccionar proveedor", list(nombres.keys()))
    prov_id = nombres[seleccion]

    try:
        reglas = proveedor_service.obtener_reglas(prov_id)
    except Exception as exc:
        notif_err(f"Error al cargar reglas: {exc}")
        return

    desc_actual    = reglas["descuento_pct"] if reglas else 0.0
    iva_actual     = reglas["iva_pct"]       if reglas else 21.0
    ganancia_actual = reglas["ganancia_pct"] if reglas else 30.0

    col_form, col_preview = st.columns([1, 1])

    with col_form:
        with st.form("form_reglas"):
            descuento = st.number_input(
                "Descuento de lista (%)", min_value=0.0, max_value=99.0,
                value=desc_actual, step=0.5, format="%.2f"
            )
            iva = st.number_input(
                "IVA (%)", min_value=0.0, max_value=50.0,
                value=iva_actual, step=0.5, format="%.2f"
            )
            ganancia = st.number_input(
                "Ganancia sobre costo (%)", min_value=0.0, max_value=500.0,
                value=ganancia_actual, step=0.5, format="%.2f"
            )
            guardar = st.form_submit_button("Guardar reglas", use_container_width=True)

        if guardar:
            try:
                proveedor_service.guardar_reglas(prov_id, descuento, iva, ganancia)
                notif_ok("Reglas guardadas correctamente.")
                st.rerun()
            except Exception as exc:
                notif_err(f"Error: {exc}")

    with col_preview:
        st.markdown("**Simulador de precio**")
        precio_ejemplo = st.number_input(
            "Precio de lista de ejemplo", min_value=0.01, value=1000.0, step=10.0
        )
        d = calcular(precio_ejemplo, descuento, iva, ganancia)
        st.markdown(
            f"""
            | Concepto | Valor |
            |----------|-------|
            | Precio lista | {fmt_moneda(d.precio_lista)} |
            | Costo real (−{fmt_pct(d.descuento_pct)}) | {fmt_moneda(d.costo_real)} |
            | Costo + IVA (+{fmt_pct(d.iva_pct)}) | {fmt_moneda(d.costo_con_iva)} |
            | **Precio venta** | **{fmt_moneda(d.precio_venta)}** |
            | Ganancia neta | {fmt_moneda(d.ganancia_neta)} |
            """
        )
        st.markdown(
            f'<div style="font-size:1.8rem; font-weight:800; color:#2ECC71">'
            f"{fmt_moneda(d.precio_venta)}</div>"
            f'<div style="color:#E74C3C; font-weight:600">'
            f"Ganancia: {fmt_moneda(d.ganancia_neta)} ({fmt_pct(d.ganancia_neta_pct)} sobre venta)</div>",
            unsafe_allow_html=True,
        )
