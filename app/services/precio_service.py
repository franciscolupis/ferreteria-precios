from dataclasses import dataclass


@dataclass
class DesglosePrecio:
    precio_lista: float
    descuento_pct: float
    iva_pct: float
    ganancia_pct: float
    costo_real: float
    costo_con_iva: float
    precio_venta: float
    ganancia_neta: float
    ganancia_neta_pct: float


def calcular(
    precio_lista: float,
    descuento_pct: float,
    iva_pct: float,
    ganancia_pct: float,
) -> DesglosePrecio:
    """
    Remarcación sobre costo (no margen sobre venta).
      costo_real    = precio_lista × (1 − descuento/100)
      costo_con_iva = costo_real   × (1 + iva/100)
      precio_venta  = costo_con_iva × (1 + ganancia/100)
    """
    costo_real = precio_lista * (1 - descuento_pct / 100)
    costo_con_iva = costo_real * (1 + iva_pct / 100)
    precio_venta = costo_con_iva * (1 + ganancia_pct / 100)
    ganancia_neta = precio_venta - costo_con_iva
    ganancia_neta_pct = (ganancia_neta / precio_venta * 100) if precio_venta else 0

    return DesglosePrecio(
        precio_lista=precio_lista,
        descuento_pct=descuento_pct,
        iva_pct=iva_pct,
        ganancia_pct=ganancia_pct,
        costo_real=costo_real,
        costo_con_iva=costo_con_iva,
        precio_venta=precio_venta,
        ganancia_neta=ganancia_neta,
        ganancia_neta_pct=ganancia_neta_pct,
    )
