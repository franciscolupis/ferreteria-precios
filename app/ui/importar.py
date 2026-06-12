import streamlit as st
from app.services import proveedor_service, producto_service, importador
from app.ui.components import notif_ok, notif_err, notif_warn, seccion
import logging

logger = logging.getLogger(__name__)


def render() -> None:
    seccion("Importar Lista de Precios")

    try:
        proveedores = proveedor_service.listar()
    except Exception as exc:
        notif_err(f"Error al cargar proveedores: {exc}")
        return

    if not proveedores:
        notif_warn("Primero crea al menos un proveedor en la pestaña correspondiente.")
        return

    nombres = {p["nombre"]: p["id"] for p in proveedores}

    with st.form("form_importar"):
        col1, col2 = st.columns(2)
        with col1:
            proveedor_sel = st.selectbox("Proveedor destino", list(nombres.keys()))
        with col2:
            archivo = st.file_uploader(
                "Archivo (Excel, CSV o PDF)",
                type=["xlsx", "xls", "csv", "pdf"],
            )

        st.markdown("---")
        st.markdown("**Mapeo de columnas** — escribí cómo se llaman en el archivo del proveedor:")

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            col_codigo = st.text_input("Código (opcional)", placeholder="ej. Código, SKU, Art.")
        with col_b:
            col_desc = st.text_input("Descripción *", value="Descripcion", placeholder="ej. Descripción, Artículo")
        with col_c:
            col_precio = st.text_input("Precio *", value="Precio", placeholder="ej. Precio, Lista, P. Lista")
        with col_d:
            col_empaque = st.text_input("Empaque (opcional)", placeholder="ej. Empaque, Presentación")

        registrar_hist = st.checkbox("Registrar historial de cambios de precio", value=True)
        importar_btn = st.form_submit_button("🚀 Importar", use_container_width=True, type="primary")

    if not importar_btn:
        _mostrar_ayuda()
        return

    if archivo is None:
        notif_warn("Seleccioná un archivo antes de importar.")
        return

    if not col_desc.strip() or not col_precio.strip():
        notif_warn("Los campos Descripción y Precio son obligatorios.")
        return

    prov_id = nombres[proveedor_sel]
    extension = archivo.name.rsplit(".", 1)[-1].lower()
    archivo_bytes = archivo.read()

    with st.spinner(f"Procesando «{archivo.name}»..."):
        try:
            if extension == "pdf":
                productos, advertencias = importador.importar_pdf(
                    archivo_bytes,
                    col_codigo=col_codigo.strip() or None,
                    col_desc=col_desc.strip(),
                    col_precio=col_precio.strip(),
                    col_empaque=col_empaque.strip() or None,
                )
            else:
                productos, advertencias = importador.importar_excel(
                    archivo_bytes,
                    col_codigo=col_codigo.strip() or None,
                    col_desc=col_desc.strip(),
                    col_precio=col_precio.strip(),
                    col_empaque=col_empaque.strip() or None,
                    extension=extension,
                )
        except ValueError as exc:
            notif_err(str(exc))
            return
        except Exception as exc:
            notif_err(f"Error inesperado al leer el archivo: {exc}")
            logger.exception("Importación fallida")
            return

    for adv in advertencias:
        notif_warn(adv)

    if not productos:
        notif_err("No se encontraron productos válidos en el archivo.")
        return

    st.info(f"Se detectaron **{len(productos)}** productos. Guardando en la base de datos...")

    # Guardar archivo original PRIMERO para obtener su ID y vincularlo con los productos
    mime_map = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls":  "application/vnd.ms-excel",
        "csv":  "text/csv",
        "pdf":  "application/pdf",
    }
    archivo_id: int | None = None
    try:
        archivo_id = proveedor_service.guardar_archivo(
            prov_id, archivo.name, archivo_bytes, mime_map.get(extension, "application/octet-stream")
        )
    except Exception as exc:
        logger.warning("No se pudo guardar el archivo original: %s", exc)

    try:
        insertados, actualizados = producto_service.insertar_lote(
            productos, prov_id, registrar_historial=registrar_hist, archivo_id=archivo_id
        )
    except Exception as exc:
        notif_err(f"Error al guardar: {exc}")
        logger.exception("Error en insertar_lote")
        return

    notif_ok(
        f"Importación exitosa — {insertados} nuevos, {actualizados} actualizados."
    )

    # Vista previa de los primeros 10
    if productos:
        st.markdown("**Vista previa (primeros 10 registros detectados):**")
        st.dataframe(
            [
                {
                    "Código": p.get("codigo_producto", ""),
                    "Descripción": p.get("descripcion", ""),
                    "Precio Lista": p.get("precio_lista", 0),
                    "Empaque": p.get("empaque", ""),
                }
                for p in productos[:10]
            ],
            use_container_width=True,
        )


def _mostrar_ayuda() -> None:
    with st.expander("ℹ️ ¿Cómo funciona el importador?"):
        st.markdown("""
**Excel / CSV**
- Lee **todas las pestañas** automáticamente.
- No asume que los encabezados están en la fila 1 — escanea dinámicamente.
- Detecta la fila de encabezados aunque haya logos, índices o texto de relleno arriba.

**PDF**
- Extrae tablas automáticamente.
- "Memoria fotográfica": aprende los índices de columna en la página donde encuentra los encabezados
  y los reutiliza en páginas posteriores que no los tienen.

**Limpieza de precios automática**
- Elimina signos `$`, espacios y saltos de línea.
- Convierte formatos conflictivos: `"6.500,50"` → `6500.50`.

**Mapeo de columnas**
- Ingresá **parte** del nombre de la columna (la búsqueda es parcial e insensible a mayúsculas).
- Ejemplo: si la columna se llama `"P. de Lista"`, podés escribir `"lista"`.
        """)
