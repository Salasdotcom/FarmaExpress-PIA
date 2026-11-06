"""Registros de venta especial (US11, US12; RNF-01, RNF-04, RNF-06).

El registro digital se origina en la revisión de receta (US09/US11) y las sustituciones (US10).
Consulta: el responsable de farmacia ve todo; el cajero ve el registro SIN datos personales de
paciente, médico y cédula; Almacén y Compras no tienen acceso."""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from src.application.base import ServicioBase
from src.domain.errors import NoEncontrado
from src.domain.permisos import exigir_rol
from src.domain.sustitucion import SustitucionDeVenta
from src.domain.value_objects import Rol
from src.domain.venta import Venta


@dataclass(frozen=True)
class RegistroEspecial:
    venta_id: str
    sucursal_id: str
    estado_venta: str
    folio_receta: Optional[str]
    resultado_revision: Optional[str]
    revisada_por: Optional[str]
    fecha_emision: Optional[date]
    datos_personales_visibles: bool
    nombre_paciente: Optional[str] = None
    nombre_medico: Optional[str] = None
    cedula_medico: Optional[str] = None
    sustituciones: list[SustitucionDeVenta] = field(default_factory=list)


def _registro(v: Venta, sustituciones: list[SustitucionDeVenta],
              completo: bool) -> RegistroEspecial:
    r = v.receta
    return RegistroEspecial(
        venta_id=v.id, sucursal_id=v.sucursal_id, estado_venta=v.estado.value,
        folio_receta=r.folio if r else None,
        resultado_revision=r.resultado.value if r and r.resultado else None,
        revisada_por=r.revisada_por if r else None,
        fecha_emision=r.fecha_emision if r else None,
        datos_personales_visibles=completo,
        nombre_paciente=r.nombre_paciente if r and completo else None,
        nombre_medico=r.medico if r and completo else None,
        cedula_medico=r.cedula_medico if r and completo else None,
        sustituciones=sustituciones)


class RegistroEspecialService(ServicioBase):
    def _acceso(self, rol: Rol) -> bool:
        """True = datos personales visibles. Lanza PermisoDenegado si el rol no puede consultar."""
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA, Rol.CAJERO)
        return rol is Rol.RESPONSABLE_FARMACIA

    def listar(self, rol: Rol, sucursal_id: Optional[str] = None,
               resultado: Optional[str] = None) -> list[RegistroEspecial]:
        completo = self._acceso(rol)
        with self._uow() as uow:
            ventas = uow.ventas.listar()
            sustituciones = uow.sustituciones.listar()
        out = []
        for v in ventas:
            sust = [s for s in sustituciones if s.venta_id == v.id]
            if v.receta is None and not sust:
                continue
            if sucursal_id and v.sucursal_id != sucursal_id:
                continue
            if resultado and not (v.receta and v.receta.resultado
                                  and v.receta.resultado.value == resultado.upper()):
                continue
            out.append(_registro(v, sust, completo))
        return out

    def obtener(self, venta_id: str, usuario: str, rol: Rol) -> RegistroEspecial:
        completo = self._acceso(rol)
        with self._uow() as uow:
            v = self._obtener(uow.ventas, venta_id, "Venta")
            sust = [s for s in uow.sustituciones.listar() if s.venta_id == v.id]
            if v.receta is None and not sust:
                raise NoEncontrado(f"La venta '{venta_id}' no tiene registro de venta especial")
            if completo:      # RNF-06: la consulta de datos personales queda auditada
                self._auditar(uow, usuario, "CONSULTAR_REGISTRO_ESPECIAL", "Venta", v.id, "", "")
                uow.commit()
            return _registro(v, sust, completo)
