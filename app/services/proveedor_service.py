import logging
from typing import Optional
from app.database.connection import db_session

logger = logging.getLogger(__name__)


def listar() -> list[dict]:
    with db_session() as conn:
        rows = conn.execute("""
            SELECT p.id, p.nombre, p.contacto, p.email,
                   r.descuento_pct, r.iva_pct, r.ganancia_pct,
                   r.col_codigo, r.col_desc, r.col_precio, r.col_empaque
            FROM proveedores p
            LEFT JOIN reglas_financieras r ON r.proveedor_id = p.id
            ORDER BY p.nombre
        """).fetchall()
        return [dict(r) for r in rows]


def crear(nombre: str, contacto: str, email: str) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO proveedores (nombre, contacto, email) VALUES (%s, %s, %s) RETURNING id",
            (nombre.strip(), contacto.strip(), email.strip()),
        )
        prov_id = cur.lastrowid
        conn.execute(
            "INSERT INTO reglas_financieras (proveedor_id) VALUES (%s)",
            (prov_id,),
        )
        logger.info("Proveedor creado: %s (id=%d)", nombre, prov_id)
        return prov_id


def actualizar(prov_id: int, nombre: str, contacto: str, email: str) -> None:
    with db_session() as conn:
        conn.execute(
            "UPDATE proveedores SET nombre=%s, contacto=%s, email=%s WHERE id=%s",
            (nombre.strip(), contacto.strip(), email.strip(), prov_id),
        )
        logger.info("Proveedor actualizado id=%d", prov_id)


def eliminar(prov_id: int) -> None:
    with db_session() as conn:
        conn.execute("DELETE FROM proveedores WHERE id=%s", (prov_id,))
        logger.warning("Proveedor eliminado id=%d", prov_id)


def obtener_reglas(prov_id: int) -> Optional[dict]:
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM reglas_financieras WHERE proveedor_id=%s", (prov_id,)
        ).fetchone()
        return dict(row) if row else None


def guardar_archivo(prov_id: int, nombre: str, contenido: bytes, mime_type: str) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO archivos_importados (proveedor_id, nombre_archivo, mime_type) "
            "VALUES (%s, %s, %s) RETURNING id",
            (prov_id, nombre, mime_type),
        )
        archivo_id = cur.lastrowid
        logger.info("Archivo registrado para proveedor id=%d: %s (archivo_id=%d)", prov_id, nombre, archivo_id)
        return archivo_id


def eliminar_archivo(archivo_id: int) -> int:
    with db_session() as conn:
        eliminados = conn.execute(
            "DELETE FROM productos WHERE archivo_origen_id = %s",
            (archivo_id,),
        ).rowcount
        conn.execute("DELETE FROM archivos_importados WHERE id = %s", (archivo_id,))
        logger.warning("Archivo id=%d eliminado — %d productos borrados", archivo_id, eliminados)
        return eliminados


def listar_archivos(prov_id: int) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, nombre_archivo, mime_type, importado_at FROM archivos_importados "
            "WHERE proveedor_id=%s ORDER BY importado_at DESC LIMIT 20",
            (prov_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def guardar_mapeo(prov_id: int, col_codigo: str, col_desc: str, col_precio: str, col_empaque: str) -> None:
    with db_session() as conn:
        conn.execute("""
            UPDATE reglas_financieras
            SET col_codigo=%s, col_desc=%s, col_precio=%s, col_empaque=%s, updated_at=CURRENT_TIMESTAMP
            WHERE proveedor_id=%s
        """, (col_codigo.strip() or None, col_desc.strip() or None,
              col_precio.strip() or None, col_empaque.strip() or None, prov_id))
        logger.info("Mapeo de columnas guardado para proveedor id=%d", prov_id)


def guardar_reglas(prov_id: int, descuento: float, iva: float, ganancia: float) -> None:
    with db_session() as conn:
        conn.execute("""
            INSERT INTO reglas_financieras (proveedor_id, descuento_pct, iva_pct, ganancia_pct)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT(proveedor_id) DO UPDATE SET
                descuento_pct = EXCLUDED.descuento_pct,
                iva_pct       = EXCLUDED.iva_pct,
                ganancia_pct  = EXCLUDED.ganancia_pct,
                updated_at    = CURRENT_TIMESTAMP
        """, (prov_id, descuento, iva, ganancia))
        logger.info("Reglas actualizadas para proveedor id=%d", prov_id)
