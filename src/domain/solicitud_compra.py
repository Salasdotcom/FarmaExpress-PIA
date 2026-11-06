"""Aggregate SolicitudDeCompra con NecesidadReposicion (US06-US08; RN-04; ADR-03)."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from src.domain.errors import InvalidTransition, ReglaDeNegocioViolada
from src.domain.events import DomainEvent
from src.domain.permisos import exigir_rol
from src.domain.value_objects import Rol


class MotivoNecesidad(str, Enum):
    FALTANTE = "FALTANTE"
    EXISTENCIA_BAJA = "EXISTENCIA_BAJA"
    CADUCADO = "CADUCADO"


class EstadoNecesidad(str, Enum):
    PENDIENTE_REVISION = "PENDIENTE_REVISION"
    CONFIRMADA = "CONFIRMADA"
    RECHAZADA = "RECHAZADA"


class EstadoSolicitud(str, Enum):
    EN_REVISION = "EN_REVISION"
    ENVIADA = "ENVIADA"


@dataclass
class NecesidadReposicion:
    id: str
    producto_id: str
    sucursal_id: str
    cantidad_requerida: int
    motivo: MotivoNecesidad
    registrada_por: str
    fecha: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    estado: EstadoNecesidad = EstadoNecesidad.PENDIENTE_REVISION
    cantidad_confirmada: Optional[int] = None
    revisada_por: Optional[str] = None

    def __post_init__(self):
        if self.cantidad_requerida <= 0:
            raise ReglaDeNegocioViolada("La cantidad requerida debe ser > 0")


@dataclass
class SolicitudDeCompra:
    id: str
    sucursal_id: str
    estado: EstadoSolicitud = EstadoSolicitud.EN_REVISION
    necesidades: list[NecesidadReposicion] = field(default_factory=list)
    solicitante_id: Optional[str] = None
    fecha_envio: Optional[datetime] = None
    events: list[DomainEvent] = field(default_factory=list)

    def _exigir_en_revision(self) -> None:
        if self.estado is not EstadoSolicitud.EN_REVISION:
            raise InvalidTransition("La solicitud ya fue enviada y no admite cambios")

    def _buscar(self, necesidad_id: str) -> NecesidadReposicion:
        for n in self.necesidades:
            if n.id == necesidad_id:
                return n
        raise ReglaDeNegocioViolada(f"La necesidad {necesidad_id} no pertenece a la solicitud")

    def registrar_necesidad(self, necesidad: NecesidadReposicion) -> None:
        self._exigir_en_revision()
        if necesidad.sucursal_id != self.sucursal_id:
            raise ReglaDeNegocioViolada("La necesidad debe ser de la sucursal de la solicitud")
        self.necesidades.append(necesidad)
        self.events.append(DomainEvent("NecesidadReposicionRegistrada", necesidad.id))

    def _revisar(self, necesidad_id: str, responsable_id: str, rol: Rol) -> NecesidadReposicion:
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        self._exigir_en_revision()
        n = self._buscar(necesidad_id)
        if n.estado is not EstadoNecesidad.PENDIENTE_REVISION:
            raise InvalidTransition("La necesidad ya fue revisada")
        n.revisada_por = responsable_id
        return n

    def confirmar_necesidad(self, necesidad_id: str, responsable_id: str, rol: Rol,
                            cantidad: Optional[int] = None) -> None:
        n = self._revisar(necesidad_id, responsable_id, rol)
        cantidad = n.cantidad_requerida if cantidad is None else cantidad
        if cantidad <= 0:
            raise ReglaDeNegocioViolada("La cantidad a solicitar debe ser > 0")
        n.estado, n.cantidad_confirmada = EstadoNecesidad.CONFIRMADA, cantidad
        self.events.append(DomainEvent("NecesidadReposicionConfirmada", n.id))

    def rechazar_necesidad(self, necesidad_id: str, responsable_id: str, rol: Rol) -> None:
        n = self._revisar(necesidad_id, responsable_id, rol)
        n.estado = EstadoNecesidad.RECHAZADA
        self.events.append(DomainEvent("NecesidadReposicionRechazada", n.id))

    @property
    def confirmadas(self) -> list[NecesidadReposicion]:
        return [n for n in self.necesidades if n.estado is EstadoNecesidad.CONFIRMADA]

    @property
    def lineas(self) -> list[tuple[str, int]]:
        """(producto, cantidad) de lo que realmente se solicita a Compras."""
        return [(n.producto_id, n.cantidad_confirmada) for n in self.confirmadas]

    def enviar(self, responsable_id: str, rol: Rol) -> None:
        """Sólo se envía con todas las necesidades revisadas y al menos una confirmada."""
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        self._exigir_en_revision()
        if any(n.estado is EstadoNecesidad.PENDIENTE_REVISION for n in self.necesidades):
            raise ReglaDeNegocioViolada("Hay necesidades pendientes de revisión")
        if not self.confirmadas:
            raise ReglaDeNegocioViolada("La solicitud requiere al menos una necesidad confirmada")
        self.estado = EstadoSolicitud.ENVIADA
        self.solicitante_id = responsable_id
        self.fecha_envio = datetime.now(timezone.utc)
        self.events.append(DomainEvent("SolicitudDeCompraEnviada", self.id))
