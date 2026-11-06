from typing import Annotated

from fastapi import APIRouter, Form

from src.api import schemas as sc
from src.api.deps import Cont, EnVentas, SoloRF
from src.api.schemas import CancelarIn, ItemIn, RecetaIn, VentaIn, VentaOut, venta_out
from src.application.venta_service import ItemVenta
from src.domain.venta import Receta

router = APIRouter(prefix="/ventas", tags=["Ventas (US02, US09, US13)"])


def _item(i: ItemIn) -> ItemVenta:
    return ItemVenta(i.producto_id, i.cantidad, i.lote_id or None)


@router.post("", response_model=VentaOut, status_code=201, summary="Crear venta EN_PROCESO")
def crear_venta(datos: Annotated[VentaIn, Form()], c: Cont, u: EnVentas):
    items = []
    if datos.producto_id:
        items.append(ItemVenta(datos.producto_id, datos.cantidad or 0, datos.lote_id or None))
    v = venta_out(c.ventas.crear_venta(datos.sucursal_id, u.id, items))
    v.mensaje = (f"Venta {v.id} creada en estado EN_PROCESO con {len(v.lineas)} línea(s); "
                 f"total {v.total} MXN. Aún no se descuenta inventario: use /completar.")
    return v


@router.get("/{venta_id}", response_model=VentaOut, summary="Consultar venta")
def obtener_venta(venta_id: str, c: Cont, u: EnVentas):
    v = venta_out(c.ventas.obtener_venta(venta_id))
    v.mensaje = f"La venta {v.id} está en estado {v.estado}."
    return v


@router.post("/{venta_id}/lineas", response_model=VentaOut,
             summary="Agregar producto a una venta EN_PROCESO")
def agregar_linea(venta_id: str, item: Annotated[ItemIn, Form()], c: Cont, u: EnVentas):
    v = venta_out(c.ventas.agregar_linea(venta_id, _item(item), u.id))
    v.mensaje = (f"Se agregó {item.cantidad} x {item.producto_id} a la venta {v.id}; "
                 f"ahora tiene {len(v.lineas)} línea(s) y total {v.total} MXN.")
    return v


@router.post("/{venta_id}/receta/revision", response_model=VentaOut,
             summary="Registrar la revisión de receta (sólo responsable de farmacia)")
def revisar_receta(venta_id: str, datos: Annotated[RecetaIn, Form()], c: Cont, u: SoloRF):
    receta = Receta(datos.folio, datos.medico, datos.cedula_medico, datos.nombre_paciente,
                    datos.fecha_emision)
    v = venta_out(c.ventas.revisar_receta(venta_id, receta, datos.resultado, u.id, u.rol))
    v.mensaje = (f"Receta {datos.folio} revisada con resultado {datos.resultado.value} "
                 f"para la venta {v.id}.")
    return v


@router.post("/{venta_id}/completar", response_model=VentaOut,
             summary="Completar venta: valida caducidad, lote, receta y existencias (DS-01/DS-02)")
def completar_venta(venta_id: str, c: Cont, u: EnVentas):
    v = venta_out(c.ventas.completar_venta(venta_id, u.id))
    v.mensaje = (f"Venta {v.id} completada: se validaron caducidad, lote, receta y existencias, "
                 f"se descontó el inventario y se cobraron {v.total} MXN.")
    return v


@router.post("/{venta_id}/cancelar", response_model=VentaOut, summary="Cancelar venta EN_PROCESO")
def cancelar_venta(venta_id: str, c: Cont, u: EnVentas, datos: Annotated[CancelarIn, Form()]):
    v = venta_out(c.ventas.cancelar_venta(venta_id, u.id, datos.motivo))
    v.mensaje = f"Venta {v.id} cancelada; no se modificó el inventario."
    return v


@router.post("/{venta_id}/sustituciones", response_model=sc.SustitucionOut, status_code=201,
             summary="Autorizar sustitución de medicamento y registrar su motivo (US10)")
def autorizar_sustitucion(venta_id: str, datos: Annotated[sc.SustitucionIn, Form()],
                          c: Cont, u: SoloRF):
    x = sc.sustitucion_out(c.ventas.autorizar_sustitucion(
        venta_id, datos.producto_solicitado, datos.alternativa_id, datos.motivo, u.id, u.rol,
        datos.lote_id or None))
    x.mensaje = (f"Sustitución autorizada: {x.producto_solicitado} → {x.alternativa}. "
                 "La línea de la venta se reemplazó y quedó registrado el responsable.")
    return x


@router.post("/{venta_id}/sustituciones/rechazo", response_model=sc.SustitucionOut,
             status_code=201, summary="Registrar que no se acepta ninguna alternativa (US10)")
def rechazar_sustitucion(venta_id: str, datos: Annotated[sc.RechazoSustitucionIn, Form()],
                         c: Cont, u: SoloRF):
    x = sc.sustitucion_out(c.ventas.rechazar_sustitucion(
        venta_id, datos.producto_solicitado, datos.motivo, u.id, u.rol))
    x.mensaje = ("Ninguna alternativa fue aceptada: la sustitución no se realizó y la venta "
                 "no cambió.")
    return x
