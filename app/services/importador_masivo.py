"""
Importador Masivo — Carpeta Local con memoria de importaciones.

Estados posibles por archivo:
  "nuevo"       → nunca fue importado
  "actualizado" → el archivo cambió desde la última importación (mtime mayor)
  "sin_cambios" → fue importado y no tuvo modificaciones
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

CARPETA_DEFAULT = Path(r"C:\Users\Usuario\Downloads\LISTAS PRECIOS-20260508T030415Z-3-001\LISTAS PRECIOS")

EXTENSIONES_PERMITIDAS = {".xlsx", ".xls", ".xlsm", ".csv", ".pdf"}

MIME_POR_EXT = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xlsm": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls":  "application/vnd.ms-excel",
    ".csv":  "text/csv",
    ".pdf":  "application/pdf",
}

ESTADO_NUEVO        = "nuevo"
ESTADO_ACTUALIZADO  = "actualizado"
ESTADO_SIN_CAMBIOS  = "sin_cambios"


@dataclass
class ResultadoArchivo:
    nombre: str
    ruta: str
    extension: str
    proveedor_id: Optional[int]      = None
    proveedor_nombre: Optional[str]  = None
    insertados: int                  = 0
    actualizados: int                = 0
    advertencias: list[str]          = field(default_factory=list)
    error: Optional[str]             = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def total(self) -> int:
        return self.insertados + self.actualizados


def _obtener_registros(carpeta: str) -> dict[str, dict]:
    from app.database.connection import db_session
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM registro_importaciones WHERE carpeta=%s", (carpeta,)
        ).fetchall()
    return {r["nombre_archivo"]: dict(r) for r in rows}


def _guardar_registro(
    nombre: str,
    carpeta: str,
    mtime: float,
    proveedor_id: int,
    proveedor_nombre: str,
    insertados: int,
    actualizados: int,
) -> None:
    from app.database.connection import db_session
    with db_session() as conn:
        conn.execute("""
            INSERT INTO registro_importaciones
                (nombre_archivo, carpeta, proveedor_id, proveedor_nombre, mtime, insertados, actualizados)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(nombre_archivo, carpeta) DO UPDATE SET
                proveedor_id     = EXCLUDED.proveedor_id,
                proveedor_nombre = EXCLUDED.proveedor_nombre,
                mtime            = EXCLUDED.mtime,
                insertados       = EXCLUDED.insertados,
                actualizados     = EXCLUDED.actualizados,
                importado_at     = CURRENT_TIMESTAMP
        """, (nombre, carpeta, proveedor_id, proveedor_nombre, mtime, insertados, actualizados))


def listar_archivos(carpeta: Path) -> list[dict]:
    if not carpeta.exists():
        raise FileNotFoundError(f"La carpeta no existe: {carpeta}")
    if not carpeta.is_dir():
        raise NotADirectoryError(f"La ruta no es una carpeta: {carpeta}")

    registros = _obtener_registros(str(carpeta))
    archivos  = []

    for f in sorted(carpeta.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() not in EXTENSIONES_PERMITIDAS:
            continue
        if f.name.endswith(".lnk"):
            continue

        stat  = f.stat()
        mtime = stat.st_mtime
        reg   = registros.get(f.name)

        if reg is None:
            estado = ESTADO_NUEVO
            ultimo_import = None
            ultimo_prov   = None
        elif mtime > reg["mtime"] + 60:
            estado = ESTADO_ACTUALIZADO
            ultimo_import = reg["importado_at"]
            ultimo_prov   = reg["proveedor_nombre"]
        else:
            estado = ESTADO_SIN_CAMBIOS
            ultimo_import = reg["importado_at"]
            ultimo_prov   = reg["proveedor_nombre"]

        archivos.append({
            "nombre":        f.name,
            "ruta":          str(f),
            "extension":     f.suffix.lower().lstrip("."),
            "modificado":    datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
            "mtime":         mtime,
            "size_kb":       round(stat.st_size / 1024, 1),
            "estado":        estado,
            "ultimo_import": str(ultimo_import or "")[:16],
            "ultimo_prov":   ultimo_prov or "",
        })

    logger.info(
        "Carpeta '%s': %d archivos — %d nuevos, %d actualizados, %d sin cambios",
        carpeta,
        len(archivos),
        sum(1 for a in archivos if a["estado"] == ESTADO_NUEVO),
        sum(1 for a in archivos if a["estado"] == ESTADO_ACTUALIZADO),
        sum(1 for a in archivos if a["estado"] == ESTADO_SIN_CAMBIOS),
    )
    return archivos


def procesar_archivo(
    ruta: str,
    nombre: str,
    extension: str,
    mtime: float,
    proveedor_id: int,
    proveedor_nombre: str,
    col_codigo: Optional[str],
    col_desc: str,
    col_precio: str,
    col_empaque: Optional[str],
    carpeta: str,
    registrar_historial: bool = True,
) -> ResultadoArchivo:
    from app.services import importador, producto_service, proveedor_service

    res = ResultadoArchivo(
        nombre=nombre, ruta=ruta, extension=extension,
        proveedor_id=proveedor_id, proveedor_nombre=proveedor_nombre,
    )

    try:
        contenido = Path(ruta).read_bytes()
    except Exception as exc:
        res.error = f"No se pudo leer el archivo: {exc}"
        return res

    try:
        if extension == "pdf":
            productos, advertencias = importador.importar_pdf(
                contenido, col_codigo, col_desc, col_precio, col_empaque
            )
        else:
            ext_norm = "xlsx" if extension == "xlsm" else extension
            productos, advertencias = importador.importar_excel(
                contenido, col_codigo, col_desc, col_precio, col_empaque, ext_norm
            )
    except Exception as exc:
        res.error = f"Error al parsear: {exc}"
        logger.error("Error parseando %s: %s", nombre, exc)
        return res

    res.advertencias = advertencias

    if not productos:
        res.error = "No se encontraron productos válidos."
        return res

    try:
        res.insertados, res.actualizados = producto_service.insertar_lote(
            productos, proveedor_id, registrar_historial=registrar_historial
        )
        mime = MIME_POR_EXT.get(f".{extension}", "application/octet-stream")
        proveedor_service.guardar_archivo(proveedor_id, nombre, contenido, mime)
        _guardar_registro(
            nombre=nombre, carpeta=carpeta, mtime=mtime,
            proveedor_id=proveedor_id, proveedor_nombre=proveedor_nombre,
            insertados=res.insertados, actualizados=res.actualizados,
        )
    except Exception as exc:
        res.error = f"Error al guardar en BD: {exc}"
        logger.error("Error guardando lote de %s: %s", nombre, exc)

    logger.info(
        "Procesado '%s' → '%s' | ins=%d act=%d",
        nombre, proveedor_nombre, res.insertados, res.actualizados,
    )
    return res
