def fmt_moneda(valor: float) -> str:
    """Formatea un float como moneda argentina: $ 1.234,56"""
    if valor is None:
        return "—"
    entero, decimal = f"{valor:,.2f}".split(".")
    entero = entero.replace(",", ".")
    return f"$ {entero},{decimal}"


def fmt_pct(valor: float) -> str:
    return f"{valor:.2f} %"


def fmt_variacion(anterior: float, nuevo: float) -> str:
    if anterior == 0:
        return "N/A"
    delta = (nuevo - anterior) / anterior * 100
    signo = "▲" if delta >= 0 else "▼"
    return f"{signo} {abs(delta):.1f} %"
