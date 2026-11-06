"""Aggregate RetiroDeLote (US03, US04; RN-02).
State machine: REGISTRADO -> EN_EJECUCION -> EJECUTADO."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from src.domain.errors import InvalidTransition, ReglaDeNegocioViolada
from src.domain.events import DomainEvent
from src.domain.lote import Lote
from src.domain.permisos import exigir_rol
from src.domain.value_objects import Rol


class EstadoRetiro(str, Enum):
    REGISTRADO = "REGISTRADO"
    EN_EJECUCION = "EN_EJECUCION"
    EJECUTADO = "EJECUTADO"


TRANSICIONES: dict[EstadoRetiro, set[EstadoRetiro]] = {
    EstadoRetiro.REGISTRADO: {EstadoRetiro.EN_EJECUCION},
    EstadoRetiro.EN_EJECUCION: {EstadoRetiro.EJECUTADO},
    EstadoRetiro.EJECUTADO: set(),
}


@dataclass(frozen=True)
class EjecucionEnSucursal:
    sucursal_id: str
    identificadas: int
    retiradas: int
    responsable_id: str
    fecha: datetime


@dataclass
class RetiroDeLote:
    id: str
    lote_id: str
    producto_id: str
    motivo: str
    registrado_por: str
    estado: EstadoRetiro = EstadoRetiro.REGISTRADO
    ejecuciones: list[EjecucionEnSucursal] = field(default_factory=list)
    en_transito_pendiente: int = 0
    events: list[DomainEvent] = field(default_factory=list)

    @classmethod
    def registrar(cls, id: str, lote: Lote, motivo: str, registrado_por: str, rol: Rol):
        """Registra el retiro confirmado y bloquea el lote en todas las sucursales."""
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        if not motivo.strip():
            raise ReglaDeNegocioViolada("El retiro requiere motivo")
        if lote.retirado:
            raise ReglaDeNegocioViolada("El lote ya está retirado")
        lote.marcar_retirado()
        retiro = cls(id, lote.id, lote.producto_id, motivo, registrado_por)
        retiro.events.append(DomainEvent("LoteRetirado", id, {"lote_id": lote.id}))
        return retiro

    def _transicionar(self, destino: EstadoRetiro) -> None:
        if destino not in TRANSICIONES[self.estado]:
            raise InvalidTransition(f"{self.estado.value} -> {destino.value} no permitida")
        self.estado = destino

    def registrar_ejecucion(self, sucursal_id: str, identificadas: int, retiradas: int,
                            responsable_id: str) -> None:
        if self.estado is EstadoRetiro.EJECUTADO:
            raise InvalidTransition("El retiro ya fue ejecutado")
        if identificadas < 0 or retiradas < 0:
            raise ReglaDeNegocioViolada("Las cantidades no pueden ser negativas")
        if retiradas > identificadas:
            raise ReglaDeNegocioViolada("No se pueden retirar más unidades de las identificadas")
        if self.estado is EstadoRetiro.REGISTRADO:
            self._transicionar(EstadoRetiro.EN_EJECUCION)
        self.ejecuciones.append(EjecucionEnSucursal(
            sucursal_id, identificadas, retiradas, responsable_id, datetime.now(timezone.utc)))

    def registrar_unidades_en_transito(self, cantidad: int) -> None:
        if self.estado is EstadoRetiro.EJECUTADO:
            raise InvalidTransition("El retiro ya fue ejecutado")
        if cantidad <= 0:
            raise ReglaDeNegocioViolada("Cantidad en tránsito debe ser > 0")
        self.en_transito_pendiente += cantidad

    def resolver_unidades_en_transito(self, cantidad: int) -> None:
        if cantidad <= 0 or cantidad > self.en_transito_pendiente:
            raise ReglaDeNegocioViolada("Cantidad a resolver inválida")
        self.en_transito_pendiente -= cantidad

    def concluir(self, responsable_id: str) -> None:
        """RN-02: no se concluye con unidades en tránsito pendientes de resolución."""
        if self.estado is not EstadoRetiro.EN_EJECUCION:
            raise InvalidTransition("Sólo un retiro EN_EJECUCION puede concluirse")
        if self.en_transito_pendiente > 0:
            raise ReglaDeNegocioViolada("Hay unidades en tránsito pendientes de resolución")
        self._transicionar(EstadoRetiro.EJECUTADO)
        self.events.append(DomainEvent("RetiroDeLoteEjecutado", self.id,
                                       {"responsable": responsable_id}))

    @property
    def total_identificadas(self) -> int:
        return sum(e.identificadas for e in self.ejecuciones)

    @property
    def total_retiradas(self) -> int:
        return sum(e.retiradas for e in self.ejecuciones)
