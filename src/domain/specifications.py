"""Specification pattern: reglas componibles con & (AND), | (OR) y ~ (NOT)."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Generic, Mapping, TypeVar

from src.domain.existencia import Existencia
from src.domain.lote import Lote
from src.domain.value_objects import EstadoVenta, ResultadoRevision
from src.domain.venta import Venta

T = TypeVar("T")


class Specification(Generic[T]):
    codigo = "SPEC"

    def is_satisfied_by(self, candidato: T) -> bool:
        raise NotImplementedError

    def __and__(self, otro: Specification[T]) -> Specification[T]:
        return _And(self, otro)

    def __or__(self, otro: Specification[T]) -> Specification[T]:
        return _Or(self, otro)

    def __invert__(self) -> Specification[T]:
        return _Not(self)


class _And(Specification):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def is_satisfied_by(self, c):
        return self.a.is_satisfied_by(c) and self.b.is_satisfied_by(c)


class _Or(Specification):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def is_satisfied_by(self, c):
        return self.a.is_satisfied_by(c) or self.b.is_satisfied_by(c)


class _Not(Specification):
    def __init__(self, a):
        self.a = a

    def is_satisfied_by(self, c):
        return not self.a.is_satisfied_by(c)


@dataclass(frozen=True)
class ContextoDeValidacion:
    venta: Venta
    hoy: date
    lotes: Mapping[str, Lote]
    existencias: Mapping[tuple, Existencia]


class VentaEnProceso(Specification[ContextoDeValidacion]):
    codigo = "VENTA_NO_EN_PROCESO"

    def is_satisfied_by(self, c):
        return c.venta.estado is EstadoVenta.EN_PROCESO and bool(c.venta.lineas)


class SinMedicamentoCaducado(Specification[ContextoDeValidacion]):
    """US02 / DS-02: ninguna línea con lote caducado (hoy >= caducidad)."""
    codigo = "MEDICAMENTO_CADUCADO"

    def is_satisfied_by(self, c):
        for linea in c.venta.lineas:
            if linea.lote_id is None:
                continue
            lote = c.lotes.get(linea.lote_id)
            if lote is None or lote.esta_caducado(c.hoy):
                return False
        return True


class SinLoteRetirado(Specification[ContextoDeValidacion]):
    """US03 / RN-02: un lote retirado se bloquea en todas las sucursales."""
    codigo = "LOTE_RETIRADO"

    def is_satisfied_by(self, c):
        return not any(
            linea.lote_id and (lote := c.lotes.get(linea.lote_id)) and lote.retirado
            for linea in c.venta.lineas
        )


class ExistenciasSuficientes(Specification[ContextoDeValidacion]):
    codigo = "EXISTENCIA_INSUFICIENTE"

    def is_satisfied_by(self, c):
        pedido: dict[tuple, int] = defaultdict(int)
        for linea in c.venta.lineas:
            pedido[(linea.producto_id, linea.lote_id, c.venta.sucursal_id)] += linea.cantidad
        for clave, cant in pedido.items():
            ex = c.existencias.get(clave)
            if ex is None or not ex.hay_disponible(cant):
                return False
        return True


class SinRecetaRequerida(Specification[ContextoDeValidacion]):
    codigo = "RECETA_REQUERIDA"

    def is_satisfied_by(self, c):
        return not c.venta.requiere_receta


class RecetaAceptada(Specification[ContextoDeValidacion]):
    """US09 / RN-05: receta incompleta, vencida o no aceptada bloquea la venta."""
    codigo = "RECETA_NO_ACEPTADA"

    def is_satisfied_by(self, c):
        r = c.venta.receta
        return r is not None and r.resultado is ResultadoRevision.ACEPTADA
