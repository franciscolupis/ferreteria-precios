import streamlit as st
from app.services import proveedor_service
from app.ui.components import notif_ok, notif_err, notif_warn, seccion


def render() -> None:
    seccion("Proveedores")
    tab_crear, tab_listar = st.tabs(["➕ Nuevo proveedor", "📋 Ver / Editar / Archivos"])

    # ── Crear ──────────────────────────────────────────────────────────────
    with tab_crear:
        with st.form("form_crear_proveedor", clear_on_submit=True):
            nombre   = st.text_input("Nombre del proveedor *")
            contacto = st.text_input("Contacto (persona)")
            email    = st.text_input("Email")
            guardar  = st.form_submit_button("Crear proveedor", use_container_width=True)

        if guardar:
            if not nombre.strip():
                notif_warn("El nombre es obligatorio.")
            else:
                try:
                    proveedor_service.crear(nombre, contacto, email)
                    notif_ok(f"Proveedor «{nombre}» creado correctamente.")
                    st.rerun()
                except Exception as exc:
                    notif_err(f"Error: {exc}")

    # ── Listar / Editar ────────────────────────────────────────────────────
    with tab_listar:
        try:
            proveedores = proveedor_service.listar()
        except Exception as exc:
            notif_err(f"Error al cargar proveedores: {exc}")
            return

        if not proveedores:
            notif_warn("No hay proveedores cargados aún.")
            return

        for p in proveedores:
            with st.expander(f"🏭 {p['nombre']}"):
                tab_datos, tab_archivos = st.tabs(["✏️ Datos", "📁 Listas importadas"])

                with tab_datos:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        with st.form(f"edit_{p['id']}"):
                            nuevo_nombre   = st.text_input("Nombre",   value=p["nombre"])
                            nuevo_contacto = st.text_input("Contacto", value=p["contacto"] or "")
                            nuevo_email    = st.text_input("Email",    value=p["email"] or "")
                            if st.form_submit_button("Guardar cambios"):
                                try:
                                    proveedor_service.actualizar(
                                        p["id"], nuevo_nombre, nuevo_contacto, nuevo_email
                                    )
                                    notif_ok("Proveedor actualizado.")
                                    st.rerun()
                                except Exception as exc:
                                    notif_err(f"Error: {exc}")

                    with col2:
                        st.markdown("<br><br>", unsafe_allow_html=True)
                        if st.button("🗑 Eliminar", key=f"del_{p['id']}", type="secondary"):
                            st.session_state[f"confirm_del_{p['id']}"] = True

                        if st.session_state.get(f"confirm_del_{p['id']}"):
                            st.warning("¿Estás seguro? Se eliminarán todos sus productos.")
                            col_si, col_no = st.columns(2)
                            with col_si:
                                if st.button("Sí, eliminar", key=f"si_{p['id']}", type="primary"):
                                    try:
                                        proveedor_service.eliminar(p["id"])
                                        st.session_state.pop(f"confirm_del_{p['id']}", None)
                                        notif_ok("Proveedor eliminado.")
                                        st.rerun()
                                    except Exception as exc:
                                        notif_err(f"Error: {exc}")
                            with col_no:
                                if st.button("Cancelar", key=f"no_{p['id']}"):
                                    st.session_state.pop(f"confirm_del_{p['id']}", None)
                                    st.rerun()

                # ── Archivos importados ────────────────────────────────────
                with tab_archivos:
                    try:
                        archivos = proveedor_service.listar_archivos(p["id"])
                    except Exception as exc:
                        notif_err(f"Error al cargar archivos: {exc}")
                        continue

                    if not archivos:
                        st.caption("Aún no hay listas importadas para este proveedor.")
                        continue

                    for arch in archivos:
                        col_a, col_b = st.columns([4, 1])
                        with col_a:
                            fecha = str(arch["importado_at"] or "")[:16]
                            st.markdown(
                                f'<span style="color:#1A1D2E">📄 **{arch["nombre_archivo"]}**</span>'
                                f'<span style="color:#6B7399; font-size:0.8rem; margin-left:12px">{fecha}</span>',
                                unsafe_allow_html=True,
                            )
                        with col_b:
                            if st.button(
                                "🗑 Eliminar",
                                key=f"del_arch_{arch['id']}",
                                type="secondary",
                                use_container_width=True,
                            ):
                                st.session_state[f"confirm_arch_{arch['id']}"] = True

                        if st.session_state.get(f"confirm_arch_{arch['id']}"):
                            st.warning(
                                f"¿Eliminar «{arch['nombre_archivo']}»? "
                                "Se borrarán los productos que fueron creados exclusivamente por esta importación."
                            )
                            col_si2, col_no2 = st.columns(2)
                            with col_si2:
                                if st.button(
                                    "Sí, eliminar",
                                    key=f"si_arch_{arch['id']}",
                                    type="primary",
                                ):
                                    try:
                                        eliminados = proveedor_service.eliminar_archivo(arch["id"])
                                        st.session_state.pop(f"confirm_arch_{arch['id']}", None)
                                        notif_ok(
                                            f"Lista eliminada. "
                                            f"{eliminados} producto(s) borrado(s) de la base de datos."
                                        )
                                        st.rerun()
                                    except Exception as exc:
                                        notif_err(f"Error al eliminar: {exc}")
                            with col_no2:
                                if st.button("Cancelar", key=f"no_arch_{arch['id']}"):
                                    st.session_state.pop(f"confirm_arch_{arch['id']}", None)
                                    st.rerun()
