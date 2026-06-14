"""
Capa de base de datos — PostgreSQL vía psycopg2.
La URL de conexión se lee de st.secrets["DATABASE_URL"].
Compatible con Supabase, Neon y cualquier proveedor PostgreSQL estándar.
"""
import logging
from contextlib import contextmanager

import streamlit as st
import psycopg2
import psycopg2.pool
import psycopg2.extras

logger = logging.getLogger(__name__)


@st.cache_resource
def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    url = st.secrets["DATABASE_URL"]
    if "sslmode" not in url:
        url += "?sslmode=require"
    pool = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=5, dsn=url)
    logger.info("Pool PostgreSQL creado.")
    return pool


class _Cursor:
    def __init__(self, pgcur):
        self._c = pgcur

    def fetchall(self) -> list:
        return self._c.fetchall()

    def fetchone(self):
        return self._c.fetchone()

    @property
    def rowcount(self) -> int:
        return self._c.rowcount

    @property
    def lastrowid(self) -> int | None:
        row = self._c.fetchone()
        return row["id"] if row else None

    def __iter__(self):
        return iter(self.fetchall())


class _Conn:
    def __init__(self, pgconn):
        self._conn = pgconn

    def execute(self, sql: str, params=None) -> _Cursor:
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        return _Cursor(cur)

    def execute_batch(self, sql: str, values: list) -> None:
        cur = self._conn.cursor()
        psycopg2.extras.execute_batch(cur, sql, values, page_size=200)

    def execute_values(self, sql: str, values: list) -> None:
        cur = self._conn.cursor()
        psycopg2.extras.execute_values(cur, sql, values, page_size=200)


@contextmanager
def db_session():
    pool = _get_pool()
    raw = pool.getconn()
    try:
        raw.autocommit = False
        yield _Conn(raw)
        raw.commit()
    except Exception as exc:
        raw.rollback()
        logger.error("DB transaction rolled back: %s", exc, exc_info=True)
        raise
    finally:
        pool.putconn(raw)


def _run_ddl(sql: str) -> None:
    try:
        with db_session() as conn:
            conn.execute(sql)
    except Exception as exc:
        logger.warning("DDL omitido (ya existe o timeout): %s", exc)


def init_db() -> None:
    with db_session() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id          SERIAL PRIMARY KEY,
                nombre      TEXT NOT NULL UNIQUE,
                contacto    TEXT,
                email       TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reglas_financieras (
                id            SERIAL PRIMARY KEY,
                proveedor_id  INTEGER NOT NULL UNIQUE
                              REFERENCES proveedores(id) ON DELETE CASCADE,
                descuento_pct REAL NOT NULL DEFAULT 0,
                iva_pct       REAL NOT NULL DEFAULT 21,
                ganancia_pct  REAL NOT NULL DEFAULT 30,
                col_codigo    TEXT,
                col_desc      TEXT,
                col_precio    TEXT,
                col_empaque   TEXT,
                updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS archivos_importados (
                id              SERIAL PRIMARY KEY,
                proveedor_id    INTEGER NOT NULL
                                REFERENCES proveedores(id) ON DELETE CASCADE,
                nombre_archivo  TEXT NOT NULL,
                contenido       BYTEA NOT NULL,
                mime_type       TEXT,
                importado_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id                SERIAL PRIMARY KEY,
                codigo_producto   TEXT,
                descripcion       TEXT NOT NULL,
                precio_lista      REAL NOT NULL,
                empaque           TEXT,
                proveedor_id      INTEGER NOT NULL
                                  REFERENCES proveedores(id) ON DELETE CASCADE,
                archivo_origen_id INTEGER
                                  REFERENCES archivos_importados(id) ON DELETE SET NULL,
                updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historial_precios (
                id                    SERIAL PRIMARY KEY,
                producto_id           INTEGER NOT NULL
                                      REFERENCES productos(id) ON DELETE CASCADE,
                precio_lista_anterior REAL,
                precio_lista_nuevo    REAL,
                motivo                TEXT,
                changed_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registro_importaciones (
                id               SERIAL PRIMARY KEY,
                nombre_archivo   TEXT NOT NULL,
                carpeta          TEXT NOT NULL,
                proveedor_id     INTEGER,
                proveedor_nombre TEXT,
                mtime            REAL NOT NULL,
                insertados       INTEGER DEFAULT 0,
                actualizados     INTEGER DEFAULT 0,
                importado_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(nombre_archivo, carpeta)
            )
        """)
    logger.info("Base de datos PostgreSQL inicializada.")

    _run_ddl("CREATE INDEX IF NOT EXISTS idx_prod_descripcion ON productos(descripcion)")
    _run_ddl("CREATE INDEX IF NOT EXISTS idx_prod_proveedor   ON productos(proveedor_id)")
    _run_ddl("CREATE INDEX IF NOT EXISTS idx_prod_codigo      ON productos(codigo_producto)")
