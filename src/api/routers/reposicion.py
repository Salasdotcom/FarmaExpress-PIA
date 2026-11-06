from typing import Annotated

from fastapi import APIRouter, Depends, Form

from src.api import schemas as s
from src.api.deps import ALMACEN, COMPRAS, RF, Cont, EnInventario, SoloRF, Usuario, con_roles

router = APIRouter(prefix="/solicitudes-compra", tags=["Reposición (US06-US08)"])
Lectores = Annotated[Usuario, Depends(con_roles(ALMACEN, RF, COMPRAS))]


@router.post("", response_model=s.SolicitudOut, status_code=201,
             summary="Crear solicitud de compra para una sucursal")
def crear_solicitud(datos: Annotated[s.SolicitudIn, Form()], c: Cont, u: EnInventario):
    r = s.solicitud_out(c.reposicion.crear_solicitud(datos.sucursal_id, u.id))
    r.mensaje = f"Solicitud {r.id} creada para {r.sucursal_id}. Agregue necesidades y envíela."
    return r


@router.get("/{solicitud_id}", response_model=s.SolicitudOut, summary="Consultar solicitud")
def obtener_solicitud(solicitud_id: str, c: Cont, u: Lectores):
    r = s.solicitud_out(c.reposicion.obtener_solicitud(solicitud_id))
    r.mensaje = f"La solicitud {r.id} está {r.estado} con {len(r.necesidades)} necesidad(es)."
    return r


@router.post("/{solicitud_id}/necesidades", response_model=s.SolicitudOut, status_code=201,
             summary="Reportar una necesidad de reposición (Almacén)")
def registrar_necesidad(solicitud_id: str, datos: Annotated[s.NecesidadIn, Form()],
                        c: Cont, u: EnInventario):
    r = s.solicitud_out(c.reposicion.registrar_necesidad(
        solicitud_id, datos.producto_id, datos.cantidad, datos.motivo, u.id))
    r.mensaje = (f"Necesidad de {datos.cantidad} x {datos.producto_id} ({datos.motivo.value}) "
                 "registrada; está pendiente de evaluación del responsable de farmacia.")
    return r


@router.post("/{solicitud_id}/necesidades/{necesidad_id}/confirmar", response_model=s.SolicitudOut,
             summary="Confirmar una necesidad (responsable de farmacia)")
def confirmar(solicitud_id: str, necesidad_id: str, c: Cont, u: SoloRF,
              datos: Annotated[s.ConfirmarIn, Form()]):
    r = s.solicitud_out(c.reposicion.confirmar_necesidad(
        solicitud_id, necesidad_id, u.id, u.rol, datos.cantidad))
    r.mensaje = f"Necesidad {necesidad_id} confirmada; se incluirá al enviar a Compras."
    return r


@router.post("/{solicitud_id}/necesidades/{necesidad_id}/rechazar", response_model=s.SolicitudOut,
             summary="Rechazar una necesidad (responsable de farmacia)")
def rechazar(solicitud_id: str, necesidad_id: str, c: Cont, u: SoloRF):
    r = s.solicitud_out(c.reposicion.rechazar_necesidad(solicitud_id, necesidad_id, u.id, u.rol))
    r.mensaje = f"Necesidad {necesidad_id} rechazada; no se enviará a Compras."
    return r


@router.post("/{solicitud_id}/enviar", response_model=s.SolicitudOut,
             summary="Enviar a Compras sólo lo confirmado (responsable de farmacia)")
def enviar(solicitud_id: str, c: Cont, u: SoloRF):
    r = s.solicitud_out(c.reposicion.enviar_solicitud(solicitud_id, u.id, u.rol))
    r.mensaje = (f"Solicitud {r.id} enviada a Compras con {len(r.lineas_a_comprar)} producto(s) "
                 "confirmado(s); lo no confirmado quedó fuera.")
    return r
