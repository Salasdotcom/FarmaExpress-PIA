"""Aggregate DiferenciaDeInventario (US15, US16; RN-08). No modifica la existencia por sí sola."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from src.domain.errors import ReglaDeNegocioViolada
from src.domain.events import DomainEvent


class EstadoInvestigacion(str, Enum):
    SIN_INVESTIGAR = "SIN_INVESTIGAR"
    CAUSA_IDENTIFICADA = "CAUSA_IDENTIFICADA"
    PENDIENTE_ACLARACION = "PENDIENTE_ACLARACION"


@dataclass
class DiferenciaDeInventario:
    id: str
    producto_id: str
    sucursal_id: str
    cantidad_registrada: int
    cantidad_fisica: int
    fecha_conteo: datetime
    usuario_responsable: str
    lote_id: Optional[str] = None
    prioritaria: bool = False  # RN-08: lote retirado, caducado, controlado o recurrente
    estado: EstadoInvestigacion = EstadoInvestigacion.SIN_INVESTIGAR
    causa_identificada: str = ""
    evidencia: str = ""
    investigador_id: Optional[str] = None
    events: list[DomainEvent] = field(default_factory=list)

    @classmethod
    def registrar(cls, id: str, producto_id: str, sucursal_id: str, cantidad_registrada: int,
                  cantidad_fisica: int, usuario_responsable: str, lote_id: Optional[str] = None,
                  prioritaria: bool = False, fecha_conteo: Optional[datetime] = None):
        if cantidad_registrada < 0 or cantidad_fisica < 0:
            raise ReglaDeNegocioViolada("Las cantidades no pueden ser negativas")
        if cantidad_registrada == cantidad_fisica:
            raise ReglaDeNegocioViolada("Sin diferencia entre cantidad física y registrada")
        dif = cls(id, producto_id, sucursal_id, cantidad_registrada, cantidad_fisica,
                  fecha_conteo or datetime.now(timezone.utc), usuario_responsable,
                  lote_id, prioritaria)
        dif.events.append(DomainEvent("DiferenciaDeInventarioRegistrada", id,
                                      {"delta": dif.delta}))
        return dif

    @property
    def delta(self) -> int:
        return self.cantidad_fisica - self.cantidad_registrada

    @property
    def clave_existencia(self) -> tuple:
        return (self.producto_id, self.lote_id, self.sucursal_id)

    def registrar_investigacion(self, investigador_id: str, causa: str = "",
                                evidencia: str = "") -> None:
        """US16: causa identificada o pendiente de aclaración (se conserva la evidencia)."""
        self.investigador_id = investigador_id
        self.evidencia = evidencia.strip()
        if causa.strip():
            self.estado = EstadoInvestigacion.CAUSA_IDENTIFICADA
            self.causa_identificada = causa.strip()
            self.events.append(DomainEvent("InvestigacionDeInventarioConcluida", self.id))
        else:
            self.estado = EstadoInvestigacion.PENDIENTE_ACLARACION
            self.causa_identificada = ""

    @property
    def ajustable(self) -> bool:
        return self.estado is EstadoInvestigacion.CAUSA_IDENTIFICADA and bool(self.evidencia)
