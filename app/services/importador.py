"""
Importador Todo Terreno
- Excel/CSV: escanea todas las pestañas, detecta la fila-encabezado dinámicamente,
  soporta columna de empaque opcional, limpia precios sucios.
- PDF: "memoria fotográfica" — memoriza índices de columna en pág. 1 y los
  reutiliza en páginas posteriores que no tienen encabezado.
"""

import re
import io
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_PRECIO_RE = re.compile(r"[^\d,.]")


# ─── Limpieza de precios ────────────────────────────────────────────────────

def _limpiar_precio(valor) -> Optional[float]:
    if valor is None:
        return None
    texto = str(valor).strip()
    texto = _PRECIO_RE.sub("", texto)
    if not texto:
        return None

    # Entero con separador de miles: "2.700", "12.500", "1.234.567"
    if re.search(r"^\d{1,3}(\.\d{3})+$", texto):
        texto = texto.replace(".", "")
    # Formato europeo con decimal: "6.500,50"  →  6500.50
    elif re.search(r"\d\.\d{3},", texto):
        texto = texto.replace(".", "").replace(",", ".")
    # Coma como decimal: "6500,50"
    elif re.search(r",\d{1,2}$", texto):
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", "")

    try:
        valor_float = float(texto)
        return valor_float if valor_float > 0 else None
    except ValueError:
        return None


# ─── Detección de fila-encabezado en DataFrame crudo ───────────────────────

def _detectar_fila_encabezado(df_raw: pd.DataFrame, cols_buscadas: list[str]) -> Optional[int]:
    """
    Recorre fila a fila buscando aquella que contiene al menos 2 de las
    palabras clave de cols_buscadas (insensible a mayúsculas y tildes).
    """
    def normalizar(s: str) -> str:
        return (
            str(s).lower()
            .replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u")
        )

    palabras = [normalizar(c) for c in cols_buscadas]

    for idx, row in df_raw.iterrows():
        valores = [normalizar(v) for v in row.values if pd.notna(v)]
        matches = sum(any(p in v for p in palabras) for v in valores)
        if matches >= 2:
            return idx
    return None


def _mapear_columnas(
    encabezados: list[str],
    col_codigo: Optional[str],
    col_desc: str,
    col_precio: str,
    col_empaque: Optional[str],
) -> dict:
    """
    Devuelve un dict {rol: índice_columna} mapeando los encabezados reales
    a los roles semánticos (codigo, descripcion, precio, empaque).
    """

    def mejor_match(objetivo: str, lista: list[str]) -> Optional[int]:
        obj = objetivo.lower()
        for i, h in enumerate(lista):
            if obj in h.lower():
                return i
        return None

    mapping = {}

    idx_desc = mejor_match(col_desc, encabezados)
    idx_precio = mejor_match(col_precio, encabezados)

    if idx_desc is None or idx_precio is None:
        raise ValueError(
            f"No se encontraron las columnas '{col_desc}' y/o '{col_precio}' "
            f"en los encabezados: {encabezados}"
        )

    mapping["descripcion"] = idx_desc
    mapping["precio"] = idx_precio

    if col_codigo:
        idx_cod = mejor_match(col_codigo, encabezados)
        if idx_cod is not None:
            mapping["codigo"] = idx_cod

    if col_empaque:
        idx_emp = mejor_match(col_empaque, encabezados)
        if idx_emp is not None:
            mapping["empaque"] = idx_emp

    return mapping


# ─── Excel / CSV ────────────────────────────────────────────────────────────

def importar_excel(
    archivo_bytes: bytes,
    col_codigo: Optional[str],
    col_desc: str,
    col_precio: str,
    col_empaque: Optional[str],
    extension: str = "xlsx",
) -> tuple[list[dict], list[str]]:
    """
    Lee TODAS las pestañas, detecta la fila encabezado en cada una y
    acumula los productos encontrados. Devuelve (productos, advertencias).
    """
    productos: list[dict] = []
    advertencias: list[str] = []

    cols_buscadas = list(filter(None, [col_codigo, col_desc, col_precio, col_empaque]))

    try:
        if extension in ("csv",):
            sheets = {"hoja1": pd.read_csv(io.BytesIO(archivo_bytes), header=None, dtype=str)}
        else:
            sheets = pd.read_excel(
                io.BytesIO(archivo_bytes),
                sheet_name=None,
                header=None,
                dtype=str,
            )
    except Exception as exc:
        raise ValueError(f"Error al leer el archivo: {exc}") from exc

    for nombre_hoja, df_raw in sheets.items():
        if df_raw.empty:
            continue

        fila_enc = _detectar_fila_encabezado(df_raw, cols_buscadas)
        if fila_enc is None:
            advertencias.append(
                f"Pestaña '{nombre_hoja}': no se encontró la fila de encabezados, omitida."
            )
            continue

        encabezados = [str(v) for v in df_raw.iloc[fila_enc].values]
        df_datos = df_raw.iloc[fila_enc + 1 :].reset_index(drop=True)

        try:
            mapping = _mapear_columnas(encabezados, col_codigo, col_desc, col_precio, col_empaque)
        except ValueError as exc:
            advertencias.append(f"Pestaña '{nombre_hoja}': {exc}")
            continue

        filas_ok = filas_err = 0
        for _, row in df_datos.iterrows():
            vals = row.tolist()
            desc = str(vals[mapping["descripcion"]]).strip() if pd.notna(vals[mapping["descripcion"]]) else ""
            precio_raw = vals[mapping["precio"]] if mapping["precio"] < len(vals) else None
            precio = _limpiar_precio(precio_raw)

            if not desc or precio is None:
                filas_err += 1
                continue

            producto = {"descripcion": desc, "precio_lista": precio}

            if "codigo" in mapping and mapping["codigo"] < len(vals):
                producto["codigo_producto"] = str(vals[mapping["codigo"]]).strip()

            if "empaque" in mapping and mapping["empaque"] < len(vals):
                emp = str(vals[mapping["empaque"]]).strip()
                producto["empaque"] = emp if emp and emp.lower() != "nan" else None

            productos.append(producto)
            filas_ok += 1

        logger.info("Pestaña '%s': %d productos, %d filas omitidas", nombre_hoja, filas_ok, filas_err)

    return productos, advertencias


# ─── PDF ────────────────────────────────────────────────────────────────────

def importar_pdf(
    archivo_bytes: bytes,
    col_codigo: Optional[str],
    col_desc: str,
    col_precio: str,
    col_empaque: Optional[str],
) -> tuple[list[dict], list[str]]:
    """
    Extrae tablas del PDF con pdfplumber.
    Memoria fotográfica: aprende los índices de columna en la primera página
    que contenga encabezados y los aplica en todas las páginas siguientes.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("Instala pdfplumber: pip install pdfplumber")

    productos: list[dict] = []
    advertencias: list[str] = []
    cols_buscadas = list(filter(None, [col_codigo, col_desc, col_precio, col_empaque]))

    mapping: Optional[dict] = None

    with pdfplumber.open(io.BytesIO(archivo_bytes)) as pdf:
        for num_pag, pagina in enumerate(pdf.pages, start=1):
            tablas = pagina.extract_tables()
            if not tablas:
                advertencias.append(f"Página {num_pag}: sin tablas detectadas.")
                continue

            for tabla in tablas:
                if not tabla:
                    continue

                filas = [[str(c).strip() if c else "" for c in fila] for fila in tabla]

                # Buscar encabezado si aún no tenemos memoria
                if mapping is None:
                    for i, fila in enumerate(filas):
                        matches = sum(
                            any(b.lower() in h.lower() for b in cols_buscadas)
                            for h in fila if h
                        )
                        if matches >= 2:
                            try:
                                mapping = _mapear_columnas(fila, col_codigo, col_desc, col_precio, col_empaque)
                                filas = filas[i + 1 :]  # cortar basura superior
                                logger.info("PDF: memoria fotográfica establecida en pág. %d — %s", num_pag, mapping)
                            except ValueError as exc:
                                advertencias.append(f"Página {num_pag}: {exc}")
                            break

                    if mapping is None:
                        advertencias.append(f"Página {num_pag}: encabezados no encontrados aún.")
                        continue

                # Extraer productos usando la memoria
                for fila in filas:
                    if not any(fila):
                        continue

                    desc_idx = mapping.get("descripcion", -1)
                    precio_idx = mapping.get("precio", -1)

                    desc = fila[desc_idx].strip() if 0 <= desc_idx < len(fila) else ""
                    precio = _limpiar_precio(fila[precio_idx] if 0 <= precio_idx < len(fila) else None)

                    if not desc or precio is None:
                        continue

                    producto = {"descripcion": desc, "precio_lista": precio}

                    cod_idx = mapping.get("codigo", -1)
                    if 0 <= cod_idx < len(fila) and fila[cod_idx]:
                        producto["codigo_producto"] = fila[cod_idx]

                    emp_idx = mapping.get("empaque", -1)
                    if 0 <= emp_idx < len(fila) and fila[emp_idx]:
                        producto["empaque"] = fila[emp_idx]

                    productos.append(producto)

    return productos, advertencias
