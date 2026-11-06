from typing import Annotated

from fastapi import APIRouter, Depends

from src.api import schemas as s
from src.api.deps import ALMACEN, COMPRAS, RF, Cont, EnInventario, SoloRF, Usuario, con_roles
from src.domain.errors import ReglaDeNegocioViolada
from src.domain.solicitud_compra import MotivoNecesidad

router = APIRouter(prefix="/solicitudes-compra", tags=["Reposición (US06-US08)"])
Lectores = Annotated[Usuario, Depends(con_roles(ALMACEN, RF, COMPRAS))]


@router.post("", response_model=s.SolicitudOut, status_code=201,
             summary="Crear solicitud de compra para una sucursal")
def crear_solicitud(datos: s.SolicitudIn, c: Cont, u: EnInventario):
    return s.solicitud_out(c.reposicion.crear_solicitud(datos.sucursal_id, u.id))


@router.get("/{solicitud_id}", response_model=s.SolicitudOut, summary="Consultar solicitud")
def obtener_solicitud(solicitud_id: str, c: Cont, u: Lectores):
    return s.solicitud_out(c.reposicion.obtener_solicitud(solicitud_id))


@router.post("/{solicitud_id}/necesidades", response_model=s.SolicitudOut, status_code=201,
             summary="Reportar una necesidad de reposición (Almacén)")
def registrar_necesidad(solicitud_id: str, datos: s.NecesidadIn, c: Cont, u: EnInventario):
    try:
        motivo = MotivoNecesidad(datos.motivo.upper())
    except ValueError:
        raise ReglaDeNegocioViolada(
            "Motivo inválido: use FALTANTE, EXISTENCIA_BAJA o CADUCADO") from None
    return s.solicitud_out(c.reposicion.registrar_necesidad(
        solicitud_id, datos.producto_id, datos.cantidad, motivo, u.id))


@router.post("/{solicitud_id}/necesidades/{necesidad_id}/confirmar", response_model=s.SolicitudOut,
             summary="Confirmar una necesidad (responsable de farmacia)")
def confirmar(solicitud_id: str, necesidad_id: str, c: Cont, u: SoloRF,
              datos: s.ConfirmarIn | None = None):
    return s.solicitud_out(c.reposicion.confirmar_necesidad(
        solicitud_id, necesidad_id, u.id, u.rol, datos.cantidad if datos else None))


@router.post("/{solicitud_id}/necesidades/{necesidad_id}/rechazar", response_model=s.SolicitudOut,
             summary="Rechazar una necesidad (responsable de farmacia)")
def rechazar(solicitud_id: str, necesidad_id: str, c: Cont, u: SoloRF):
    return s.solicitud_out(c.reposicion.rechazar_necesidad(solicitud_id, necesidad_id, u.id, u.rol))


@router.post("/{solicitud_id}/enviar", response_model=s.SolicitudOut,
             summary="Enviar a Compras sólo lo confirmado (responsable de farmacia)")
def enviar(solicitud_id: str, c: Cont, u: SoloRF):
    return s.solicitud_out(c.reposicion.enviar_solicitud(solicitud_id, u.id, u.rol))
