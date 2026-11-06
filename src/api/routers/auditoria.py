from typing import Optional

from fastapi import APIRouter

from src.api.deps import Cont, SoloRF
from src.api.schemas import AuditoriaOut, auditoria_out

router = APIRouter(prefix="/auditoria", tags=["Auditoría (RF-16)"])


@router.get("", response_model=list[AuditoriaOut],
            summary="Historial de acciones (sólo responsable de farmacia, RNF-01)")
def consultar(c: Cont, u: SoloRF, entidad_id: Optional[str] = None, accion: Optional[str] = None):
    return [auditoria_out(r) for r in c.auditoria.consultar(entidad_id, accion)]
