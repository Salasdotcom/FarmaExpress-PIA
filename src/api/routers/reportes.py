from datetime import date
from enum import Enum
from typing import Optional

from fastapi import APIRouter

from src.api import schemas as sc
from src.api.deps import Autenticado, Cont
from src.application.reporte_service import Filtros

router = APIRouter(prefix="/reportes", tags=["Reportes (US18)"])


class TipoReporte(str, Enum):
    caducidad = "caducidad"
    retiros = "retiros"
    diferencias = "diferencias"
    ajustes = "ajustes"
    solicitudes = "solicitudes"
    ventas_especiales = "ventas_especiales"


@router.get("/{tipo}", response_model=sc.ReporteOut,
            summary="Reporte operativo con filtros por sucursal, producto, lote, estado y periodo")
def reporte(tipo: TipoReporte, c: Cont, u: Autenticado, sucursal_id: Optional[str] = None,
            producto_id: Optional[str] = None, lote_id: Optional[str] = None,
            estado: Optional[str] = None, desde: Optional[date] = None,
            hasta: Optional[date] = None):
    r = sc.reporte_out(c.reportes.generar(
        tipo.value, u.rol, Filtros(sucursal_id, producto_id, lote_id, estado, desde, hasta)))
    r.mensaje = f"Reporte de {r.tipo}: {r.total} registro(s) con los filtros indicados."
    return r
