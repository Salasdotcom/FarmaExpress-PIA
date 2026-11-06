"""Consulta de la bitácora (RF-16). El control de acceso lo aplica la API (RNF-01)."""
from typing import Optional

from src.application.base import ServicioBase
from src.domain.auditoria import RegistroAuditoria


class AuditoriaApplicationService(ServicioBase):
    def consultar(self, entidad_id: Optional[str] = None,
                  accion: Optional[str] = None) -> list[RegistroAuditoria]:
        with self._uow() as uow:
            registros = uow.historial.listar()
        if entidad_id:
            registros = [r for r in registros if r.entidad_id == entidad_id]
        if accion:
            registros = [r for r in registros if r.accion == accion.upper()]
        return registros
