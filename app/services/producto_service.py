import logging
from app.database.connection import db_session

logger = logging.getLogger(__name__)


def buscar(termino: str, proveedor_id: int | None = None) -> list[dict]:
    patron = f"%{termino.strip()}%"
    filtro_prov = "AND pr.proveedor_id = %s" if proveedor_id else ""
    params: list = [patron, patron]
    if proveedor_id:
        params.append(proveedor_id)

    with db_session() as conn:
        rows = conn.execute(f"""
            SELECT
                pr.id, pr.codigo_producto, pr.descripcion,
                pr.precio_lista, pr.empaque, pr.updated_at,
                p.id AS proveedor_id, p.nombre AS proveedor,
                r.descuento_pct, r.iva_pct, r.ganancia_pct
            FROM productos pr
            JOIN proveedores p ON p.id = pr.proveedor_id
            LEFT JOIN reglas_financieras r ON r.proveedor_id = pr.proveedor_id
            WHERE (pr.descripcion ILIKE %s OR pr.codigo_producto ILIKE %s)
            {filtro_prov}
            ORDER BY pr.descripcion
            LIMIT 200
        """, params).fetchall()
        return [dict(r) for r in rows]


def insertar_lote(
    productos: list[dict],
    proveedor_id: int,
    registrar_historial: bool = True,
    archivo_id: int | None = None,
) -> tuple[int, int]:
    insertados = actualizados = 0

    with db_session() as conn:
        for p in productos:
            codigo = (p.get("codigo_producto") or "").strip() or None
            desc = (p.get("descripcion") or "").strip()
            precio = float(p.get("precio_lista", 0))
            empaque = (p.get("empaque") or "").strip() or None

            if not desc or precio <= 0:
                continue

            if codigo:
                existing = conn.execute(
                    "SELECT id, precio_lista FROM productos WHERE codigo_producto=%s AND proveedor_id=%s",
                    (codigo, proveedor_id),
                ).fetchone()
            else:
                existing = conn.execute(
                    "SELECT id, precio_lista FROM productos WHERE descripcion=%s AND proveedor_id=%s",
                    (desc, proveedor_id),
                ).fetchone()

            if existing:
                if registrar_historial and existing["precio_lista"] != precio:
                    conn.execute(
                        """INSERT INTO historial_precios
                           (producto_id, precio_lista_anterior, precio_lista_nuevo, motivo)
                           VALUES (%s, %s, %s, 'importacion')""",
                        (existing["id"], existing["precio_lista"], precio),
                    )
                conn.execute(
                    """UPDATE productos
                       SET descripcion=%s, precio_lista=%s, empaque=%s, updated_at=CURRENT_TIMESTAMP
                       WHERE id=%s""",
                    (desc, precio, empaque, existing["id"]),
                )
                actualizados += 1
            else:
                conn.execute(
                    """INSERT INTO productos
                       (codigo_producto, descripcion, precio_lista, empaque, proveedor_id, archivo_origen_id)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (codigo, desc, precio, empaque, proveedor_id, archivo_id),
                )
                insertados += 1

    logger.info("Lote guardado — insertados: %d, actualizados: %d", insertados, actualizados)
    return insertados, actualizados


def historial_producto(producto_id: int) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            """SELECT precio_lista_anterior, precio_lista_nuevo, motivo, changed_at
               FROM historial_precios WHERE producto_id=%s ORDER BY changed_at DESC LIMIT 50""",
            (producto_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def stats_generales() -> dict:
    with db_session() as conn:
        total_productos   = conn.execute("SELECT COUNT(*) AS total FROM productos").fetchone()["total"]
        total_proveedores = conn.execute("SELECT COUNT(*) AS total FROM proveedores").fetchone()["total"]
        precio_promedio   = conn.execute("SELECT AVG(precio_lista) AS avg FROM productos").fetchone()["avg"] or 0
        ultima_actualizacion = conn.execute(
            "SELECT MAX(updated_at) AS max FROM productos"
        ).fetchone()["max"]
        return {
            "total_productos": total_productos,
            "total_proveedores": total_proveedores,
            "precio_promedio": precio_promedio,
            "ultima_actualizacion": ultima_actualizacion,
        }
