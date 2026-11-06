"""Errores de dominio -> HTTP: 404, 403, 409, 422 (y 400 si la solicitud está mal formada)."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.domain.errors import (
    InvalidTransition,
    NoEncontrado,
    PermisoDenegado,
    ReglaDeNegocioViolada,
    ValidacionDeVentaFallida,
)

EXPLICACIONES = {
    "VENTA_NO_EN_PROCESO": "La venta ya no está EN_PROCESO, no puede modificarse.",
    "MEDICAMENTO_CADUCADO": "Hay un medicamento caducado (hoy o antes): no es vendible.",
    "LOTE_RETIRADO": "Hay un lote con retiro vigente: está bloqueado para la venta.",
    "EXISTENCIA_INSUFICIENTE": "No hay piezas suficientes en la sucursal para esa cantidad.",
    "RECETA_REQUERIDA": "Un producto exige receta y la venta no tiene una registrada.",
    "RECETA_NO_ACEPTADA": "La receta no fue aceptada por el responsable de farmacia.",
}


def _resp(status: int, codigo: str, detalle: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={"codigo": codigo, "detalle": detalle, **extra})


def registrar_errores(app: FastAPI) -> None:
    @app.exception_handler(NoEncontrado)
    async def _404(_: Request, e: NoEncontrado):
        return _resp(404, "NO_ENCONTRADO", str(e))

    @app.exception_handler(PermisoDenegado)
    async def _403(_: Request, e: PermisoDenegado):
        return _resp(403, "PERMISO_DENEGADO", str(e))

    @app.exception_handler(InvalidTransition)
    async def _409(_: Request, e: InvalidTransition):
        return _resp(409, "TRANSICION_INVALIDA", str(e))

    @app.exception_handler(ValidacionDeVentaFallida)
    async def _422_venta(_: Request, e: ValidacionDeVentaFallida):
        explicacion = [EXPLICACIONES.get(v, v) for v in e.violaciones]
        return _resp(422, "VENTA_NO_COMPLETABLE", str(e), violaciones=list(e.violaciones),
                     explicacion=explicacion)

    @app.exception_handler(ReglaDeNegocioViolada)
    async def _422(_: Request, e: ReglaDeNegocioViolada):
        return _resp(422, "REGLA_DE_NEGOCIO", str(e))

    @app.exception_handler(RequestValidationError)
    async def _400(_: Request, e: RequestValidationError):
        errores = [{"campo": ".".join(str(x) for x in err["loc"]), "mensaje": err["msg"]}
                   for err in e.errors()]
        return _resp(400, "SOLICITUD_INVALIDA", "La solicitud está mal formada", errores=errores)
