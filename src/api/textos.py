"""Textos legibles para los mensajes de la API (sin folios ni nombres internos)."""


def legible(valor) -> str:
    """CADUCADO -> 'caducado'; EN_PROCESO -> 'en proceso'."""
    return str(getattr(valor, "value", valor)).replace("_", " ").lower()
