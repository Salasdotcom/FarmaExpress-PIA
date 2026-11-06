"""Value Objects y enums del dominio (VO-01..VO-04 de la AF3)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from src.domain.errors import ReglaDeNegocioViolada

UMBRAL_CRITICO_DIAS = 10   # RN-01
UMBRAL_PROXIMO_DIAS = 90   # RN-01


class EstadoVenta(str, Enum):
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"


class ClasificacionDeCaducidad(str, Enum):
    NORMAL = "NORMAL"
    PROXIMO = "PROXIMO_A_CADUCAR"
    CRITICO = "CRITICO"
    CADUCADO = "CADUCADO"


class CategoriaProducto(str, Enum):
    VENTA_LIBRE = "VENTA_LIBRE"
    RECETA_SIMPLE = "RECETA_SIMPLE"
    CONTROLADO = "CONTROLADO"


class ResultadoRevision(str, Enum):
    ACEPTADA = "ACEPTADA"
    INCOMPLETA = "INCOMPLETA"
    VENCIDA = "VENCIDA"
    NO_ACEPTADA = "NO_ACEPTADA"


def clasificar_caducidad(fecha_caducidad: date, hoy: date) -> ClasificacionDeCaducidad:
    """RN-01 / US01. Caducado desde el mismo día de la fecha de caducidad."""
    dias = (fecha_caducidad - hoy).days
    if dias <= 0:
        return ClasificacionDeCaducidad.CADUCADO
    if dias <= UMBRAL_CRITICO_DIAS:
        return ClasificacionDeCaducidad.CRITICO
    if dias <= UMBRAL_PROXIMO_DIAS:
        return ClasificacionDeCaducidad.PROXIMO
    return ClasificacionDeCaducidad.NORMAL


@dataclass(frozen=True)
class Cantidad:
    valor: int

    def __post_init__(self):
        if not isinstance(self.valor, int) or isinstance(self.valor, bool) or self.valor < 0:
            raise ReglaDeNegocioViolada("Cantidad inválida: debe ser entero >= 0")


@dataclass(frozen=True)
class Dinero:
    monto: Decimal
    moneda: str = "MXN"

    def __post_init__(self):
        if not isinstance(self.monto, Decimal) or not self.monto.is_finite() or self.monto < 0:
            raise ReglaDeNegocioViolada("Monto inválido")

    def por(self, factor: int) -> Dinero:
        return Dinero(self.monto * factor, self.moneda)

    def sumar(self, otro: Dinero) -> Dinero:
        if self.moneda != otro.moneda:
            raise ReglaDeNegocioViolada("Monedas distintas")
        return Dinero(self.monto + otro.monto, self.moneda)


class Rol(str, Enum):
    CAJERO = "CAJERO"
    RESPONSABLE_FARMACIA = "RESPONSABLE_FARMACIA"
    ALMACEN = "ALMACEN"
    COMPRAS = "COMPRAS"
