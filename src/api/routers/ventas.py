from fastapi import APIRouter

from src.api.deps import Cont, EnVentas, SoloRF
from src.api.schemas import CancelarIn, ItemIn, RecetaIn, VentaIn, VentaOut, venta_out
from src.application.venta_service import ItemVenta
from src.domain.venta import Receta

router = APIRouter(prefix="/ventas", tags=["Ventas (US02, US09, US13)"])


def _item(i: ItemIn) -> ItemVenta:
    return ItemVenta(i.producto_id, i.cantidad, i.lote_id)


@router.post("", response_model=VentaOut, status_code=201, summary="Crear venta EN_PROCESO")
def crear_venta(datos: VentaIn, c: Cont, u: EnVentas):
    return venta_out(c.ventas.crear_venta(datos.sucursal_id, u.id, [_item(i) for i in datos.items]))


@router.get("/{venta_id}", response_model=VentaOut, summary="Consultar venta")
def obtener_venta(venta_id: str, c: Cont, u: EnVentas):
    return venta_out(c.ventas.obtener_venta(venta_id))


@router.post("/{venta_id}/lineas", response_model=VentaOut,
             summary="Agregar producto a una venta EN_PROCESO")
def agregar_linea(venta_id: str, item: ItemIn, c: Cont, u: EnVentas):
    return venta_out(c.ventas.agregar_linea(venta_id, _item(item), u.id))


@router.post("/{venta_id}/receta/revision", response_model=VentaOut,
             summary="Registrar la revisión de receta (sólo responsable de farmacia)")
def revisar_receta(venta_id: str, datos: RecetaIn, c: Cont, u: SoloRF):
    receta = Receta(datos.folio, datos.medico, datos.cedula_medico, datos.nombre_paciente,
                    datos.fecha_emision)
    return venta_out(c.ventas.revisar_receta(venta_id, receta, datos.resultado, u.id, u.rol))


@router.post("/{venta_id}/completar", response_model=VentaOut,
             summary="Completar venta: valida caducidad, lote, receta y existencias (DS-01/DS-02)")
def completar_venta(venta_id: str, c: Cont, u: EnVentas):
    return venta_out(c.ventas.completar_venta(venta_id, u.id))


@router.post("/{venta_id}/cancelar", response_model=VentaOut, summary="Cancelar venta EN_PROCESO")
def cancelar_venta(venta_id: str, c: Cont, u: EnVentas, datos: CancelarIn | None = None):
    return venta_out(c.ventas.cancelar_venta(venta_id, u.id, datos.motivo if datos else ""))
