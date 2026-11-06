"""Reportes operativos (US18, RF-15): filtros por sucursal, producto, lote, estado y periodo
cuando son aplicables. Roles: responsable de farmacia, Almacén y Compras (RNF-01)."""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.application.base import ServicioBase
from src.domain.errors import ReglaDeNegocioViolada
from src.domain.permisos import exigir_rol
from src.domain.value_objects import Rol

TIPOS = ("caducidad", "retiros", "diferencias", "ajustes", "solicitudes", "ventas_especiales")


@dataclass(frozen=True)
class Filtros:
    sucursal_id: Optional[str] = None
    producto_id: Optional[str] = None
    lote_id: Optional[str] = None
    estado: Optional[str] = None
    desde: Optional[date] = None
    hasta: Optional[date] = None


@dataclass(frozen=True)
class Reporte:
    tipo: str
    total: int
    filas: list[dict]


def _ok(valor, filtro) -> bool:
    return filtro is None or filtro == "" or valor == filtro


def _en_periodo(d: date, f: Filtros) -> bool:
    return (f.desde is None or d >= f.desde) and (f.hasta is None or d <= f.hasta)


class ReporteService(ServicioBase):
    def generar(self, tipo: str, rol: Rol, filtros: Filtros) -> Reporte:
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA, Rol.ALMACEN, Rol.COMPRAS)
        if tipo not in TIPOS:
            raise ReglaDeNegocioViolada(f"Tipo de reporte inválido; use: {', '.join(TIPOS)}")
        filas = getattr(self, f"_{tipo}")(filtros)
        return Reporte(tipo, len(filas), filas)

    def _caducidad(self, f: Filtros) -> list[dict]:
        hoy = self._clock.hoy()
        with self._uow() as uow:
            lotes = {lt.id: lt for lt in uow.lotes.listar()}
            existencias = uow.existencias.listar()
        filas = []
        for e in existencias:
            lote = lotes.get(e.lote_id)
            if lote is None:
                continue
            clasif = lote.clasificacion(hoy).value
            if not (_ok(e.sucursal_id, f.sucursal_id) and _ok(e.producto_id, f.producto_id)
                    and _ok(e.lote_id, f.lote_id) and _ok(clasif, f.estado and f.estado.upper())
                    and _en_periodo(lote.fecha_caducidad, f)):
                continue
            filas.append({"sucursal_id": e.sucursal_id, "producto_id": e.producto_id,
                          "lote_id": e.lote_id, "cantidad": e.cantidad,
                          "fecha_caducidad": lote.fecha_caducidad.isoformat(),
                          "dias_restantes": (lote.fecha_caducidad - hoy).days,
                          "clasificacion": clasif, "retirado": lote.retirado})
        return sorted(filas, key=lambda x: x["dias_restantes"])

    def _retiros(self, f: Filtros) -> list[dict]:
        with self._uow() as uow:
            retiros = uow.retiros.listar()
        filas = []
        for r in retiros:
            sucursales = {e.sucursal_id for e in r.ejecuciones}
            if not (_ok(r.producto_id, f.producto_id) and _ok(r.lote_id, f.lote_id)
                    and _ok(r.estado.value, f.estado and f.estado.upper())):
                continue
            if f.sucursal_id and f.sucursal_id not in sucursales:
                continue
            filas.append({"retiro_id": r.id, "lote_id": r.lote_id, "producto_id": r.producto_id,
                          "estado": r.estado.value, "motivo": r.motivo,
                          "identificadas": r.total_identificadas, "retiradas": r.total_retiradas,
                          "en_transito_pendiente": r.en_transito_pendiente,
                          "sucursales": sorted(sucursales)})
        return filas

    def _diferencias(self, f: Filtros) -> list[dict]:
        with self._uow() as uow:
            difs = uow.diferencias.listar()
        return [{"diferencia_id": d.id, "sucursal_id": d.sucursal_id, "producto_id": d.producto_id,
                 "lote_id": d.lote_id, "cantidad_registrada": d.cantidad_registrada,
                 "cantidad_fisica": d.cantidad_fisica, "delta": d.delta,
                 "estado": d.estado.value, "prioritaria": d.prioritaria,
                 "fecha_conteo": d.fecha_conteo.date().isoformat()}
                for d in difs
                if _ok(d.sucursal_id, f.sucursal_id) and _ok(d.producto_id, f.producto_id)
                and _ok(d.lote_id, f.lote_id) and _ok(d.estado.value, f.estado and f.estado.upper())
                and _en_periodo(d.fecha_conteo.date(), f)]

    def _ajustes(self, f: Filtros) -> list[dict]:
        with self._uow() as uow:
            ajustes = uow.ajustes.listar()
            difs = {d.id: d for d in uow.diferencias.listar()}
        filas = []
        for a in ajustes:
            d = difs.get(a.diferencia_id)
            sucursal, producto, lote = (d.sucursal_id, d.producto_id, d.lote_id) if d else (
                None, None, None)
            if not (_ok(sucursal, f.sucursal_id) and _ok(producto, f.producto_id)
                    and _ok(lote, f.lote_id) and _ok(a.estado.value, f.estado and f.estado.upper())
                    and _en_periodo(a.fecha.date(), f)):
                continue
            filas.append({"ajuste_id": a.id, "diferencia_id": a.diferencia_id,
                          "sucursal_id": sucursal, "producto_id": producto, "lote_id": lote,
                          "cantidad_anterior": a.cantidad_anterior,
                          "cantidad_nueva": a.cantidad_nueva, "estado": a.estado.value,
                          "ejecutor_id": a.ejecutor_id, "autorizador_id": a.autorizador_id,
                          "fecha": a.fecha.date().isoformat()})
        return filas

    def _solicitudes(self, f: Filtros) -> list[dict]:
        with self._uow() as uow:
            sols = uow.solicitudes.listar()
        filas = []
        for s in sols:
            primera = min((n.fecha for n in s.necesidades), default=None)
            if not (_ok(s.sucursal_id, f.sucursal_id) and _ok(s.estado.value,
                                                              f.estado and f.estado.upper())):
                continue
            if f.producto_id and not any(n.producto_id == f.producto_id for n in s.necesidades):
                continue
            if primera and not _en_periodo(primera.date(), f):
                continue
            horas = None
            if primera and s.fecha_envio:
                horas = round((s.fecha_envio - primera).total_seconds() / 3600, 2)
            filas.append({"solicitud_id": s.id, "sucursal_id": s.sucursal_id,
                          "estado": s.estado.value, "necesidades": len(s.necesidades),
                          "confirmadas": len(s.confirmadas),
                          "primera_necesidad": primera.isoformat() if primera else None,
                          "fecha_envio": s.fecha_envio.isoformat() if s.fecha_envio else None,
                          "horas_hasta_envio": horas})
        return filas

    def _ventas_especiales(self, f: Filtros) -> list[dict]:
        """Sin datos personales de paciente/médico: el reporte sólo cuenta y clasifica."""
        with self._uow() as uow:
            ventas = uow.ventas.listar()
            sustituciones = uow.sustituciones.listar()
        filas = []
        for v in ventas:
            sust = [x for x in sustituciones if x.venta_id == v.id]
            if v.receta is None and not sust:
                continue
            resultado = v.receta.resultado.value if v.receta and v.receta.resultado else None
            productos = {li.producto_id for li in v.lineas}
            if not (_ok(v.sucursal_id, f.sucursal_id) and _ok(v.estado.value,
                                                              f.estado and f.estado.upper())
                    and (not f.producto_id or f.producto_id in productos)
                    and (not f.lote_id or any(li.lote_id == f.lote_id for li in v.lineas))):
                continue
            if (f.desde or f.hasta) and (v.receta is None
                                         or not _en_periodo(v.receta.fecha_emision, f)):
                continue      # el periodo se mide por la fecha de la receta
            filas.append({"venta_id": v.id, "sucursal_id": v.sucursal_id,
                          "estado_venta": v.estado.value, "resultado_revision": resultado,
                          "revisada_por": v.receta.revisada_por if v.receta else None,
                          "sustituciones": len(sust),
                          "fecha_receta": v.receta.fecha_emision.isoformat() if v.receta else None})
        return filas
