"""Aggregate AjusteDeInventario (US17; RN-09; ADR-02).
State machine: PENDIENTE -> AUTORIZADO -> APLICADO  |  PENDIENTE -> RECHAZADO."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from src.domain.diferencia import DiferenciaDeInventario
from src.domain.errors import InvalidTransition, PermisoDenegado, ReglaDeNegocioViolada
from src.domain.events import DomainEvent
from src.domain.existencia import Existencia
from src.domain.permisos import exigir_rol
from src.domain.value_objects import Rol


class EstadoAjuste(str, Enum):
    PENDIENTE = "PENDIENTE"
    AUTORIZADO = "AUTORIZADO"
    APLICADO = "APLICADO"
    RECHAZADO = "RECHAZADO"


TRANSICIONES: dict[EstadoAjuste, set[EstadoAjuste]] = {
    EstadoAjuste.PENDIENTE: {EstadoAjuste.AUTORIZADO, EstadoAjuste.RECHAZADO},
    EstadoAjuste.AUTORIZADO: {EstadoAjuste.APLICADO},
    EstadoAjuste.APLICADO: set(),
    EstadoAjuste.RECHAZADO: set(),
}


@dataclass
class AjusteDeInventario:
    id: str
    diferencia_id: str
    clave_existencia: tuple
    cantidad_anterior: int
    cantidad_nueva: int
    motivo: str
    evidencia: str
    ejecutor_id: str
    fecha: datetime
    estado: EstadoAjuste = EstadoAjuste.PENDIENTE
    autorizador_id: Optional[str] = None
    events: list[DomainEvent] = field(default_factory=list)

    @classmethod
    def solicitar(cls, id: str, diferencia: DiferenciaDeInventario, ejecutor_id: str, motivo: str):
        """El ajuste requiere una diferencia investigada con causa y evidencia (RN-09)."""
        if not diferencia.ajustable:
            raise ReglaDeNegocioViolada(
                "La diferencia debe tener causa identificada y evidencia antes de ajustar")
        if not motivo.strip():
            raise ReglaDeNegocioViolada("El ajuste requiere motivo")
        return cls(id, diferencia.id, diferencia.clave_existencia, diferencia.cantidad_registrada,
                   diferencia.cantidad_fisica, motivo.strip(), diferencia.evidencia, ejecutor_id,
                   datetime.now(timezone.utc))

    def _transicionar(self, destino: EstadoAjuste) -> None:
        if destino not in TRANSICIONES[self.estado]:
            raise InvalidTransition(f"{self.estado.value} -> {destino.value} no permitida")
        self.estado = destino

    def _validar_autorizador(self, autorizador_id: str, rol: Rol) -> None:
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        if autorizador_id == self.ejecutor_id:
            raise PermisoDenegado("Quien ejecuta el ajuste no puede autorizar su propia corrección")

    def autorizar(self, autorizador_id: str, rol: Rol) -> None:
        self._validar_autorizador(autorizador_id, rol)
        self._transicionar(EstadoAjuste.AUTORIZADO)
        self.autorizador_id = autorizador_id
        self.events.append(DomainEvent("AjusteDeInventarioAutorizado", self.id,
                                       {"autorizador": autorizador_id}))

    def rechazar(self, autorizador_id: str, rol: Rol) -> None:
        self._validar_autorizador(autorizador_id, rol)
        self._transicionar(EstadoAjuste.RECHAZADO)
        self.autorizador_id = autorizador_id

    def aplicar(self, existencia: Existencia) -> None:
        """La existencia sólo cambia al aplicar un ajuste autorizado."""
        if self.estado is not EstadoAjuste.AUTORIZADO:
            raise InvalidTransition("Sólo se aplican ajustes AUTORIZADOS")
        if existencia.clave != self.clave_existencia:
            raise ReglaDeNegocioViolada("La existencia no corresponde al ajuste")
        if existencia.cantidad != self.cantidad_anterior:
            raise ReglaDeNegocioViolada("La existencia cambió desde que se registró la diferencia")
        existencia.aplicar_ajuste(self.cantidad_nueva)
        self._transicionar(EstadoAjuste.APLICADO)
        self.events.append(DomainEvent("AjusteDeInventarioAplicado", self.id))
