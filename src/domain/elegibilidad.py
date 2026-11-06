"""Reglas ilustrativas del paquete de pruebas del profesor, como Specifications componibles.

NO sustituyen los requerimientos del BRD: son el "modelo de pruebas propuesto" del PIA
(puede_procesarse y beneficio_referencia). Reutilizan el patrón Specification del dominio.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.domain.specifications import Specification
from src.domain.value_objects import Dinero

UMBRAL_BENEFICIO = Decimal("1500")


@dataclass(frozen=True)
class OperacionEvaluable:
    operacion_id: str
    actor_id: str
    actor_activo: bool
    actor_preferente: bool
    numero_de_lineas: int
    total: Dinero
    promocion_activa: bool
    autorizada: bool


class ActorActivo(Specification[OperacionEvaluable]):
    codigo = "ACTOR_INACTIVO"

    def is_satisfied_by(self, op: OperacionEvaluable) -> bool:
        return op.actor_activo


class OperacionConLineas(Specification[OperacionEvaluable]):
    codigo = "SIN_LINEAS"

    def is_satisfied_by(self, op: OperacionEvaluable) -> bool:
        return op.numero_de_lineas > 0


class OperacionAutorizada(Specification[OperacionEvaluable]):
    codigo = "SIN_AUTORIZACION"

    def is_satisfied_by(self, op: OperacionEvaluable) -> bool:
        return op.autorizada


class ActorPreferente(Specification[OperacionEvaluable]):
    codigo = "NO_PREFERENTE"

    def is_satisfied_by(self, op: OperacionEvaluable) -> bool:
        return op.actor_preferente


class TotalMinimo(Specification[OperacionEvaluable]):
    codigo = "TOTAL_INSUFICIENTE"

    def __init__(self, minimo: Decimal = UMBRAL_BENEFICIO):
        self.minimo = minimo

    def is_satisfied_by(self, op: OperacionEvaluable) -> bool:
        return op.total.monto >= self.minimo


class PromocionActiva(Specification[OperacionEvaluable]):
    codigo = "PROMOCION_ACTIVA"

    def is_satisfied_by(self, op: OperacionEvaluable) -> bool:
        return op.promocion_activa


# Composiciones (AND / NOT) tal como las pide el paquete
puede_procesarse = ActorActivo() & OperacionConLineas() & OperacionAutorizada()
beneficio_referencia = ActorPreferente() & TotalMinimo() & ~PromocionActiva()

# (código de incumplimiento, especificación atómica) para explicar por qué falla una composición
_PROCESAR = (("ACTOR_INACTIVO", ActorActivo()), ("SIN_LINEAS", OperacionConLineas()),
             ("SIN_AUTORIZACION", OperacionAutorizada()))
_BENEFICIO = (("NO_PREFERENTE", ActorPreferente()), ("TOTAL_INSUFICIENTE", TotalMinimo()),
              ("PROMOCION_ACTIVA", ~PromocionActiva()))


@dataclass(frozen=True)
class Dictamen:
    cumple: bool
    incumplidas: tuple[str, ...]


def _dictamen(spec: Specification, atomicas, op: OperacionEvaluable) -> Dictamen:
    faltan = tuple(codigo for codigo, a in atomicas if not a.is_satisfied_by(op))
    return Dictamen(spec.is_satisfied_by(op), faltan)


def evaluar_procesable(op: OperacionEvaluable) -> Dictamen:
    return _dictamen(puede_procesarse, _PROCESAR, op)


def evaluar_beneficio(op: OperacionEvaluable) -> Dictamen:
    return _dictamen(beneficio_referencia, _BENEFICIO, op)
