"""Sustitución de medicamento en una venta (US10, RF-18/RF-16).

Sólo el responsable de farmacia decide. Si autoriza, queda registrado el producto solicitado,
la alternativa, el motivo y el responsable; si no acepta ninguna alternativa, se registra la
decisión y la venta no cambia."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src.domain.errors import ReglaDeNegocioViolada
from src.domain.events import DomainEvent
from src.domain.permisos import exigir_rol
from src.domain.value_objects import Rol


class EstadoSustitucion(str, Enum):
    AUTORIZADA = "AUTORIZADA"
    RECHAZADA = "RECHAZADA"


@dataclass
class SustitucionDeVenta:
    id: str
    venta_id: str
    producto_solicitado: str
    motivo: str
    responsable_id: str
    fecha: datetime
    estado: EstadoSustitucion
    alternativa: Optional[str] = None
    events: list[DomainEvent] = field(default_factory=list)

    @classmethod
    def autorizar(cls, id: str, venta_id: str, producto_solicitado: str, alternativa: str,
                  motivo: str, responsable_id: str, rol: Rol, fecha: datetime):
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        if not motivo.strip():
            raise ReglaDeNegocioViolada("La sustitución requiere motivo")
        if not alternativa or alternativa == producto_solicitado:
            raise ReglaDeNegocioViolada("La alternativa debe ser distinta al producto solicitado")
        s = cls(id, venta_id, producto_solicitado, motivo.strip(), responsable_id, fecha,
                EstadoSustitucion.AUTORIZADA, alternativa)
        s.events.append(DomainEvent("SustitucionAutorizada", id, {
            "venta": venta_id, "solicitado": producto_solicitado, "alternativa": alternativa}))
        return s

    @classmethod
    def rechazar(cls, id: str, venta_id: str, producto_solicitado: str, motivo: str,
                 responsable_id: str, rol: Rol, fecha: datetime):
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        if not motivo.strip():
            raise ReglaDeNegocioViolada("La decisión requiere motivo")
        s = cls(id, venta_id, producto_solicitado, motivo.strip(), responsable_id, fecha,
                EstadoSustitucion.RECHAZADA)
        s.events.append(DomainEvent("SustitucionRechazada", id, {"venta": venta_id}))
        return s
