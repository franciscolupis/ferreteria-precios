"""UI para importación masiva con memoria de estado por archivo."""
import streamlit as st
from pathlib import Path
from datetime import datetime
from app.services import proveedor_service
from app.services import importador_masivo as im
from app.services.importador_masivo import ESTADO_NUEVO, ESTADO_ACTUALIZADO, ESTADO_SIN_CAMBIOS
from app.ui.components import notif_ok, notif_err, notif_warn, seccion


# ── Helpers visuales ──────────────────────────────────────────────────────────

def _icono_ext(ext: str) -> str:
    return {"pdf": "📕", "xlsx": "📗", "xls": "📗", "xlsm": "📗", "csv": "📄"}.get(ext, "📁")


ESTADO_CFG = {
    ESTADO_NUEVO:       {"color": "#1E9E55", "bg": "#EBF9F1", "border": "#A8DBBE", "label": "NUEVO",        "dot": "🟢"},
    ESTADO_ACTUALIZADO: {"color": "#D97706", "bg": "#FEF9EC", "border": "#F3C86D", "label": "ACTUALIZADO",  "dot": "🟡"},
    ESTADO_SIN_CAMBIOS: {"color": "#94A3B8", "bg": "#F8F9FB", "border": "#DDE0E8", "label": "SIN CAMBIOS",  "dot": "⚪"},
}

def _badge_estado(estado: str) -> str:
    c = ESTADO_CFG[estado]
    return (f'<span style="background:{c["bg"]}; color:{c["color"]}; '
            f'border:1px solid {c["border"]}; border-radius:20px; '
            f'padding:1px 8px; font-size:0.68rem; font-weight:700; white-space:nowrap">'
            f'{c["label"]}</span>')

def _badge_mapeo(tiene: bool) -> str:
    if tiene:
        return ('<span style="background:#EBF9F1; color:#1E9E55; border:1px solid #A8DBBE;'
                ' border-radius:20px; padding:2px 9px; font-size:0.72rem; font-weight:700"> ✓ Mapeo guardado</span>')
    return ('<span style="background:#FEF9EC; color:#7B5A00; border:1px solid #F3C86D;'
            ' border-radius:20px; padding:2px 9px; font-size:0.72rem; font-weight:700"> ⚠ Sin mapeo</span>')


# ── Render principal ──────────────────────────────────────────────────────────

def render() -> None:
    seccion("Importación Masiva — Carpeta Local")

    # ── Selector de carpeta ────────────────────────────────────────────────
    carpeta_default = str(im.CARPETA_DEFAULT)
    st.markdown('<div style="font-size:0.8rem; color:#8A8FA8; margin-bottom:4px">Ruta de la carpeta</div>',
                unsafe_allow_html=True)

    carpeta_str = st.text_input(
        "Ruta", value=st.session_state.get("carpeta_masivo", carpeta_default),
        label_visibility="collapsed", key="carpeta_masivo_input",
    )

    col_scan, col_abrir, _ = st.columns([1, 1, 3])
    with col_scan:
        escanear = st.button("🔍 Escanear carpeta", use_container_width=True, type="primary")
    with col_abrir:
        if st.button("📂 Abrir en explorador", use_container_width=True):
            import subprocess
            try:
                subprocess.Popen(f'explorer "{carpeta_str}"')
            except Exception:
                notif_warn("No se pudo abrir el explorador.")

    if escanear:
        with st.spinner("Escaneando y verificando historial..."):
            try:
                archivos = im.listar_archivos(Path(carpeta_str.strip()))
                st.session_state["drive_archivos"]    = archivos
                st.session_state["carpeta_masivo"]    = carpeta_str.strip()
                st.session_state.pop("drive_asignaciones", None)
                # Auto-seleccionar solo nuevos y actualizados
                st.session_state["drive_sel"] = {
                    a["ruta"]: a["estado"] in (ESTADO_NUEVO, ESTADO_ACTUALIZADO)
                    for a in archivos
                }
                n_new = sum(1 for a in archivos if a["estado"] == ESTADO_NUEVO)
                n_upd = sum(1 for a in archivos if a["estado"] == ESTADO_ACTUALIZADO)
                n_ok  = sum(1 for a in archivos if a["estado"] == ESTADO_SIN_CAMBIOS)
                notif_ok(
                    f"{len(archivos)} archivos encontrados — "
                    f"🟢 {n_new} nuevos · 🟡 {n_upd} actualizados · ⚪ {n_ok} sin cambios. "
                    f"Se pre-seleccionaron los {n_new + n_upd} que necesitan importarse."
                )
            except FileNotFoundError as exc:
                notif_err(str(exc)); st.session_state.pop("drive_archivos", None); return
            except Exception as exc:
                notif_err(f"Error: {exc}"); return

    archivos = st.session_state.get("drive_archivos")
    if not archivos:
        st.markdown(
            '<div style="text-align:center; padding:48px 20px">'
            '<div style="font-size:2.5rem; margin-bottom:10px">📂</div>'
            '<p style="color:#A0A8C0; font-size:0.9rem">'
            'Escaneá la carpeta para ver el estado de cada lista.</p></div>',
            unsafe_allow_html=True,
        )
        return

    # ── Resumen de estados ─────────────────────────────────────────────────
    n_new = sum(1 for a in archivos if a["estado"] == ESTADO_NUEVO)
    n_upd = sum(1 for a in archivos if a["estado"] == ESTADO_ACTUALIZADO)
    n_ok  = sum(1 for a in archivos if a["estado"] == ESTADO_SIN_CAMBIOS)
    n_sel = sum(1 for a in archivos if st.session_state.get("drive_sel", {}).get(a["ruta"]))

    for col, val, label, color, bg in zip(
        st.columns(4),
        [n_new, n_upd, n_ok, n_sel],
        ["Nuevos", "Actualizados", "Sin cambios", "Seleccionados"],
        ["#1E9E55", "#D97706", "#94A3B8", "#FF6B35"],
        ["#EBF9F1", "#FEF9EC", "#F8F9FB", "#FFF3EE"],
    ):
        with col:
            st.markdown(
                f'<div style="background:{bg}; border:1px solid {color}33; border-radius:8px;'
                f' padding:12px; text-align:center">'
                f'<div style="font-size:1.6rem; font-weight:800; color:{color}">{val}</div>'
                f'<div style="font-size:0.72rem; color:{color}; opacity:.8; margin-top:2px">{label}</div>'
                f'</div>', unsafe_allow_html=True,
            )

    # ── Cargar proveedores ─────────────────────────────────────────────────
    try:
        proveedores = proveedor_service.listar()
    except Exception as exc:
        notif_err(f"No se pudieron cargar proveedores: {exc}"); return

    if not proveedores:
        notif_warn("Primero creá al menos un proveedor."); return

    prov_por_nombre = {p["nombre"]: p for p in proveedores}
    nombres_prov    = list(prov_por_nombre.keys())

    if "drive_asignaciones" not in st.session_state:
        # Pre-asignar por último proveedor conocido en el registro
        st.session_state["drive_asignaciones"] = {
            a["ruta"]: a["ultimo_prov"] if a["ultimo_prov"] in prov_por_nombre else nombres_prov[0]
            for a in archivos
        }

    # ── PASO 1: Lista de archivos con estado ──────────────────────────────
    seccion("Paso 1 — Archivos encontrados")

    col_filtro, col_acciones = st.columns([2, 2])
    with col_filtro:
        mostrar = st.radio(
            "Mostrar",
            ["Todos", "Solo nuevos y actualizados", "Solo sin cambios"],
            horizontal=True, label_visibility="collapsed",
        )
    with col_acciones:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sel. nuevos/actualizados", use_container_width=True):
                st.session_state["drive_sel"] = {
                    a["ruta"]: a["estado"] in (ESTADO_NUEVO, ESTADO_ACTUALIZADO)
                    for a in archivos
                }
                st.rerun()
        with c2:
            if st.button("⬜ Deseleccionar todos", use_container_width=True):
                st.session_state["drive_sel"] = {a["ruta"]: False for a in archivos}
                st.rerun()

    # Filtrar según selección
    if mostrar == "Solo nuevos y actualizados":
        archivos_vis = [a for a in archivos if a["estado"] in (ESTADO_NUEVO, ESTADO_ACTUALIZADO)]
    elif mostrar == "Solo sin cambios":
        archivos_vis = [a for a in archivos if a["estado"] == ESTADO_SIN_CAMBIOS]
    else:
        archivos_vis = archivos

    # Encabezado tabla
    st.markdown("""
    <div style="display:grid; grid-template-columns:28px 80px 1fr 180px;
         padding:6px 10px; font-size:0.67rem; font-weight:700; color:#A0A8C0;
         text-transform:uppercase; letter-spacing:0.8px;
         border-bottom:1px solid #E4E6EB; background:#F8F9FB; border-radius:8px 8px 0 0">
      <span></span><span>Estado</span><span>Archivo</span><span>Proveedor</span>
    </div>""", unsafe_allow_html=True)

    for arch in archivos_vis:
        ruta   = arch["ruta"]
        estado = arch["estado"]
        cfg    = ESTADO_CFG[estado]

        col_chk, col_est, col_info, col_prov = st.columns([0.22, 0.7, 3, 1.8])

        with col_chk:
            st.session_state["drive_sel"][ruta] = st.checkbox(
                "", value=st.session_state["drive_sel"].get(ruta, False), key=f"chk_{ruta}"
            )
        with col_est:
            subtexto = ""
            if estado == ESTADO_SIN_CAMBIOS and arch["ultimo_import"]:
                subtexto = f'<div style="font-size:0.65rem; color:#A0A8C0">{arch["ultimo_import"]}</div>'
            elif estado == ESTADO_ACTUALIZADO and arch["ultimo_import"]:
                subtexto = f'<div style="font-size:0.65rem; color:#D97706">prev: {arch["ultimo_import"]}</div>'
            st.markdown(
                f'<div style="padding:5px 0">{_badge_estado(estado)}{subtexto}</div>',
                unsafe_allow_html=True,
            )
        with col_info:
            st.markdown(
                f'<div style="padding:5px 0; border-bottom:1px solid #F0F2F5; font-size:0.84rem">'
                f'{_icono_ext(arch["extension"])} '
                f'<span style="color:#1A1D2E; font-weight:500">{arch["nombre"]}</span>'
                f'<span style="color:#A0A8C0; font-size:0.72rem; margin-left:8px">'
                f'{arch["modificado"]} · {arch["size_kb"]} KB</span></div>',
                unsafe_allow_html=True,
            )
        with col_prov:
            actual  = st.session_state["drive_asignaciones"].get(ruta, nombres_prov[0])
            if actual not in prov_por_nombre:
                actual = nombres_prov[0]
            elegido = st.selectbox(
                "p", nombres_prov,
                index=nombres_prov.index(actual),
                key=f"prov_{ruta}", label_visibility="collapsed",
            )
            st.session_state["drive_asignaciones"][ruta] = elegido

    # ── PASO 2: Mapeo por proveedor ────────────────────────────────────────
    seleccionados = [a for a in archivos if st.session_state["drive_sel"].get(a["ruta"])]
    provs_en_uso: dict[str, dict] = {}
    for a in seleccionados:
        np = st.session_state["drive_asignaciones"].get(a["ruta"], nombres_prov[0])
        if np not in provs_en_uso:
            provs_en_uso[np] = prov_por_nombre[np]

    if not provs_en_uso:
        st.markdown("<br>", unsafe_allow_html=True)
        notif_warn("Seleccioná al menos un archivo para importar.")
        return

    seccion("Paso 2 — Mapeo de columnas por proveedor")
    st.markdown(
        '<p style="color:#8A8FA8; font-size:0.82rem; margin-bottom:12px">'
        'Configurá el nombre de las columnas del archivo de cada proveedor. '
        '<b>Se guarda para siempre</b> — la próxima vez es automático.</p>',
        unsafe_allow_html=True,
    )

    if "mapeos_editados" not in st.session_state:
        st.session_state["mapeos_editados"] = {}

    for nombre_prov, pdata in provs_en_uso.items():
        tiene_mapeo = bool(pdata.get("col_desc"))
        n_arch = sum(
            1 for a in seleccionados
            if st.session_state["drive_asignaciones"].get(a["ruta"]) == nombre_prov
        )

        st.markdown(
            f'<div style="background:#FFFFFF; border:1px solid #E4E6EB; border-radius:10px;'
            f' padding:16px 20px; margin-bottom:10px">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px">'
            f'<span style="font-weight:700; color:#1A1D2E; font-size:0.95rem">🏭 {nombre_prov}'
            f'<span style="color:#A0A8C0; font-weight:400; font-size:0.78rem; margin-left:8px">'
            f'{n_arch} archivo(s)</span></span>'
            f'{_badge_mapeo(tiene_mapeo)}</div>',
            unsafe_allow_html=True,
        )

        sm    = st.session_state["mapeos_editados"].get(nombre_prov, {})
        ckey  = nombre_prov.replace(" ", "_").replace("/", "_")
        v_cod  = sm.get("col_codigo",  pdata.get("col_codigo")  or "")
        v_desc = sm.get("col_desc",    pdata.get("col_desc")    or "Descripcion")
        v_prec = sm.get("col_precio",  pdata.get("col_precio")  or "Precio")
        v_emp  = sm.get("col_empaque", pdata.get("col_empaque") or "")

        c1, c2, c3, c4, c5 = st.columns([1, 1.2, 1.2, 1, 0.8])
        with c1: nuevo_cod  = st.text_input("Código (opc.)",  value=v_cod,  key=f"mc_cod_{ckey}",  placeholder="Cod, Art, SKU")
        with c2: nuevo_desc = st.text_input("Descripción *",  value=v_desc, key=f"mc_desc_{ckey}")
        with c3: nuevo_prec = st.text_input("Precio *",       value=v_prec, key=f"mc_prec_{ckey}")
        with c4: nuevo_emp  = st.text_input("Empaque (opc.)", value=v_emp,  key=f"mc_emp_{ckey}",  placeholder="UxB, Empaque")
        with c5:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Guardar", key=f"save_{ckey}", use_container_width=True):
                if not nuevo_desc.strip() or not nuevo_prec.strip():
                    notif_warn(f"{nombre_prov}: Descripción y Precio son obligatorios.")
                else:
                    try:
                        proveedor_service.guardar_mapeo(pdata["id"], nuevo_cod, nuevo_desc, nuevo_prec, nuevo_emp)
                        pdata.update({"col_codigo": nuevo_cod, "col_desc": nuevo_desc,
                                      "col_precio": nuevo_prec, "col_empaque": nuevo_emp})
                        notif_ok(f"Mapeo de {nombre_prov} guardado.")
                        st.rerun()
                    except Exception as exc:
                        notif_err(f"Error: {exc}")

        st.session_state["mapeos_editados"][nombre_prov] = {
            "col_codigo": nuevo_cod, "col_desc": nuevo_desc,
            "col_precio": nuevo_prec, "col_empaque": nuevo_emp,
        }
        st.markdown("</div>", unsafe_allow_html=True)

    # ── PASO 3: Importar ───────────────────────────────────────────────────
    seccion("Paso 3 — Importar")

    registrar_hist = st.checkbox("Registrar historial de cambios de precio", value=True)

    # Contar estados de los seleccionados
    n_nv = sum(1 for a in seleccionados if a["estado"] == ESTADO_NUEVO)
    n_up = sum(1 for a in seleccionados if a["estado"] == ESTADO_ACTUALIZADO)
    n_sc = sum(1 for a in seleccionados if a["estado"] == ESTADO_SIN_CAMBIOS)
    resumen_sel = []
    if n_nv: resumen_sel.append(f"🟢 {n_nv} nuevos")
    if n_up: resumen_sel.append(f"🟡 {n_up} actualizados")
    if n_sc: resumen_sel.append(f"⚪ {n_sc} sin cambios")

    st.markdown("<br>", unsafe_allow_html=True)

    if not st.button(
        f"🚀 Importar {len(seleccionados)} archivo(s)  —  {' · '.join(resumen_sel)}",
        type="primary", use_container_width=True, disabled=len(seleccionados) == 0,
    ):
        return

    for np in provs_en_uso:
        m = st.session_state["mapeos_editados"].get(np, {})
        if not m.get("col_desc") or not m.get("col_precio"):
            notif_err(f"Completá el mapeo de {np} antes de importar."); return

    # ── Ejecutar ───────────────────────────────────────────────────────────
    carpeta_actual = st.session_state.get("carpeta_masivo", "")
    barra = st.progress(0, text="Iniciando...")
    resultados = []

    for i, a in enumerate(seleccionados):
        np    = st.session_state["drive_asignaciones"].get(a["ruta"], nombres_prov[0])
        pdata = prov_por_nombre[np]
        m     = st.session_state["mapeos_editados"].get(np, {})

        barra.progress(int(i / len(seleccionados) * 100), text=f"Procesando {a['nombre']}…")

        res = im.procesar_archivo(
            ruta=a["ruta"], nombre=a["nombre"], extension=a["extension"],
            mtime=a["mtime"], proveedor_id=pdata["id"], proveedor_nombre=np,
            col_codigo=m.get("col_codigo") or None,
            col_desc=m.get("col_desc", "Descripcion"),
            col_precio=m.get("col_precio", "Precio"),
            col_empaque=m.get("col_empaque") or None,
            carpeta=carpeta_actual,
            registrar_historial=registrar_hist,
        )
        resultados.append(res)

    barra.progress(100, text="Completado.")
    barra.empty()

    # Actualizar estados en session_state para reflejar lo importado
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    for r, a in zip(resultados, seleccionados):
        if r.ok:
            a["estado"]        = ESTADO_SIN_CAMBIOS
            a["ultimo_import"] = ahora

    # ── Resumen ────────────────────────────────────────────────────────────
    seccion("Resultado")

    ok_c  = sum(1 for r in resultados if r.ok)
    err_c = len(resultados) - ok_c
    ins_t = sum(r.insertados for r in resultados)
    act_t = sum(r.actualizados for r in resultados)

    for col, val, label, color in zip(
        st.columns(4),
        [ok_c, err_c, ins_t, act_t],
        ["Archivos OK", "Con errores", "Productos nuevos", "Actualizados"],
        ["#1E9E55", "#E74C3C", "#FF6B35", "#3498DB"],
    ):
        with col:
            st.markdown(
                f'<div style="background:#FFFFFF; border:1px solid #E4E6EB; border-radius:8px;'
                f' padding:14px; text-align:center">'
                f'<div style="font-size:1.8rem; font-weight:800; color:{color}">{val}</div>'
                f'<div style="font-size:0.75rem; color:#A0A8C0; margin-top:4px">{label}</div>'
                f'</div>', unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    for r in resultados:
        color  = "#1E9E55" if r.ok else "#E74C3C"
        detalle = f"nuevos: {r.insertados} · actualizados: {r.actualizados}" if r.ok else r.error
        st.markdown(
            f'<div style="display:flex; justify-content:space-between; padding:8px 14px;'
            f' background:#FFFFFF; border:1px solid #E4E6EB; border-left:3px solid {color};'
            f' border-radius:8px; margin-bottom:5px; font-size:0.84rem">'
            f'<span><b style="color:{color}">{"✓" if r.ok else "✕"}</b> '
            f'<span style="color:#1A1D2E">{r.nombre}</span>'
            f'<span style="color:#A0A8C0; font-size:0.73rem"> · {r.proveedor_nombre}</span></span>'
            f'<span style="color:{color}; font-size:0.82rem">{detalle}</span></div>',
            unsafe_allow_html=True,
        )
        for adv in r.advertencias:
            st.caption(f"  ⚠ {adv}")

    if ok_c > 0:
        notif_ok(f"Importación completa. Próximo escaneo mostrará estos {ok_c} archivos como ⚪ Sin cambios.")
