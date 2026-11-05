"""DS-01 ServicioDeValidacionDeVenta (flujos DS-01 y DS-02)."""
from dataclasses import dataclass
from functools import reduce

from src.domain.specifications import (
    ContextoDeValidacion,
    ExistenciasSuficientes,
    RecetaAceptada,
    SinLoteRetirado,
    SinMedicamentoCaducado,
    SinRecetaRequerida,
    Specification,
    VentaEnProceso,
)


@dataclass(frozen=True)
class ResultadoValidacion:
    valida: bool
    violaciones: tuple[str, ...] = ()


class ServicioDeValidacionDeVenta:
    def __init__(self):
        self._reglas: list[Specification] = [
            VentaEnProceso(),
            SinMedicamentoCaducado(),
            SinLoteRetirado(),
            SinRecetaRequerida() | RecetaAceptada(),
            ExistenciasSuficientes(),
        ]
        self._reglas[3].codigo = RecetaAceptada.codigo

    def especificacion_completa(self) -> Specification:
        return reduce(lambda a, b: a & b, self._reglas)

    def validar(self, ctx: ContextoDeValidacion) -> ResultadoValidacion:
        fallos = tuple(r.codigo for r in self._reglas if not r.is_satisfied_by(ctx))
        return ResultadoValidacion(valida=not fallos, violaciones=fallos)
