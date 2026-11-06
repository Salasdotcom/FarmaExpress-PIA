from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RegistroAuditoria:
    """RF-16: quién hizo qué, cuándo, y el estado antes/después."""
    usuario: str
    accion: str
    entidad: str
    entidad_id: str
    antes: str
    despues: str
    fecha: datetime
