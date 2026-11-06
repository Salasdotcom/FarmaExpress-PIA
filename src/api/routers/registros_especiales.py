from typing import Optional

from fastapi import APIRouter

from src.api import schemas as sc
from src.api.deps import Autenticado, Cont

router = APIRouter(prefix="/registros-especiales", tags=["Ventas especiales (US11, US12)"])


@router.get("", response_model=list[sc.RegistroEspecialOut],
            summary="Consultar registros de venta especial según permisos (US12)")
def listar(c: Cont, u: Autenticado, sucursal_id: Optional[str] = None,
           resultado: Optional[str] = None):
    regs = [sc.registro_out(r) for r in c.registros.listar(u.rol, sucursal_id, resultado)]
    for r in regs:
        r.mensaje = ("Datos personales visibles (responsable de farmacia)."
                     if r.datos_personales_visibles else
                     "Datos personales de paciente y médico restringidos para su rol.")
    return regs


@router.get("/{venta_id}", response_model=sc.RegistroEspecialOut,
            summary="Consultar un registro de venta especial (queda auditado)")
def obtener(venta_id: str, c: Cont, u: Autenticado):
    r = sc.registro_out(c.registros.obtener(venta_id, u.id, u.rol))
    r.mensaje = ("Registro completo; la consulta quedó auditada." if r.datos_personales_visibles
                 else "Registro sin datos personales de paciente ni médico (rol sin permiso).")
    return r
