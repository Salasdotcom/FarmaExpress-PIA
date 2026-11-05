"""Domain Events (DE-01..DE-08). Hechos ya ocurridos; sin infraestructura de mensajería."""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DomainEvent:
    nombre: str
    agregado_id: str
    datos: dict = field(default_factory=dict)
    ocurrido_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
