"""Repositorios SQLAlchemy: traducen entre filas (models.py) y agregados del dominio."""
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.ajuste import AjusteDeInventario, EstadoAjuste
from src.domain.auditoria import RegistroAuditoria
from src.domain.diferencia import DiferenciaDeInventario, EstadoInvestigacion
from src.domain.existencia import Existencia
from src.domain.lote import Lote
from src.domain.producto import Producto
from src.domain.retiro import EjecucionEnSucursal, EstadoRetiro, RetiroDeLote
from src.domain.solicitud_compra import (
    EstadoNecesidad,
    EstadoSolicitud,
    MotivoNecesidad,
    NecesidadReposicion,
    SolicitudDeCompra,
)
from src.domain.sustitucion import EstadoSustitucion, SustitucionDeVenta
from src.domain.value_objects import CategoriaProducto, Dinero, EstadoVenta, ResultadoRevision
from src.domain.venta import LineaDeVenta, Receta, Venta
from src.infrastructure import models as m


class _SqlRepo:
    modelo: type

    def __init__(self, session: Session):
        self._s = session

    def obtener(self, id: str) -> Optional[Any]:
        fila = self._s.get(self.modelo, id)
        return None if fila is None else self._a_dominio(fila)

    def guardar(self, entidad: Any) -> None:
        self._s.merge(self._a_fila(entidad))

    def listar(self) -> list:
        return [self._a_dominio(f) for f in self._s.scalars(select(self.modelo))]

    def _a_fila(self, entidad):
        raise NotImplementedError

    def _a_dominio(self, fila):
        raise NotImplementedError


class SqlProductoRepo(_SqlRepo):
    modelo = m.ProductoRow

    def _a_fila(self, p: Producto):
        return m.ProductoRow(id=p.id, descripcion=p.descripcion, precio=p.precio.monto,
                             categoria=p.categoria.value, habilitado=p.habilitado)

    def _a_dominio(self, f) -> Producto:
        return Producto(f.id, f.descripcion, Dinero(f.precio), CategoriaProducto(f.categoria),
                        f.habilitado)


class SqlLoteRepo(_SqlRepo):
    modelo = m.LoteRow

    def _a_fila(self, lote: Lote):
        return m.LoteRow(id=lote.id, producto_id=lote.producto_id,
                         fecha_caducidad=lote.fecha_caducidad, retirado=lote.retirado)

    def _a_dominio(self, f) -> Lote:
        return Lote(f.id, f.producto_id, f.fecha_caducidad, f.retirado)


def _clave(producto_id: str, lote_id: Optional[str], sucursal_id: str) -> str:
    return f"{producto_id}|{lote_id or ''}|{sucursal_id}"


class SqlExistenciaRepo(_SqlRepo):
    modelo = m.ExistenciaRow

    def obtener(self, producto_id, lote_id, sucursal_id):
        # FOR UPDATE en PostgreSQL: dos ventas simultáneas no descuentan la misma existencia.
        fila = self._s.get(m.ExistenciaRow, _clave(producto_id, lote_id, sucursal_id),
                           with_for_update=True)
        return None if fila is None else self._a_dominio(fila)

    def listar_por_producto(self, producto_id):
        filas = self._s.scalars(select(m.ExistenciaRow).where(
            m.ExistenciaRow.producto_id == producto_id).order_by(m.ExistenciaRow.clave))
        return [self._a_dominio(f) for f in filas]

    def guardar(self, e: Existencia) -> None:
        self._s.merge(self._a_fila(e))

    def _a_fila(self, e: Existencia):
        return m.ExistenciaRow(clave=_clave(e.producto_id, e.lote_id, e.sucursal_id),
                               producto_id=e.producto_id, lote_id=e.lote_id,
                               sucursal_id=e.sucursal_id, cantidad=e.cantidad)

    def _a_dominio(self, f) -> Existencia:
        return Existencia(f.producto_id, f.sucursal_id, f.cantidad, f.lote_id)


class SqlVentaRepo(_SqlRepo):
    modelo = m.VentaRow

    def _a_fila(self, v: Venta):
        r = v.receta
        return m.VentaRow(
            id=v.id, sucursal_id=v.sucursal_id, cajero_id=v.cajero_id, estado=v.estado.value,
            observaciones=v.observaciones, correcciones=list(v.correcciones),
            receta_folio=r.folio if r else None, receta_medico=r.medico if r else None,
            receta_cedula=r.cedula_medico if r else None,
            receta_paciente=r.nombre_paciente if r else None,
            receta_fecha=r.fecha_emision if r else None,
            receta_resultado=r.resultado.value if r and r.resultado else None,
            receta_revisada_por=r.revisada_por if r else None,
            lineas=[m.LineaVentaRow(orden=i, producto_id=li.producto_id, cantidad=li.cantidad,
                                    precio_unitario=li.precio_unitario.monto, lote_id=li.lote_id,
                                    requiere_receta=li.requiere_receta)
                    for i, li in enumerate(v.lineas)])

    def _a_dominio(self, f) -> Venta:
        receta = None
        if f.receta_folio is not None:
            receta = Receta(
                f.receta_folio, f.receta_medico, f.receta_cedula, f.receta_paciente,
                f.receta_fecha,
                ResultadoRevision(f.receta_resultado) if f.receta_resultado else None,
                f.receta_revisada_por)
        lineas = [LineaDeVenta(li.producto_id, li.cantidad, Dinero(li.precio_unitario),
                               li.lote_id, li.requiere_receta) for li in f.lineas]
        return Venta(f.id, f.sucursal_id, f.cajero_id, EstadoVenta(f.estado), lineas, receta,
                     f.observaciones, list(f.correcciones or []))


class SqlSustitucionRepo(_SqlRepo):
    modelo = m.SustitucionRow

    def _a_fila(self, s: SustitucionDeVenta):
        return m.SustitucionRow(
            id=s.id, venta_id=s.venta_id, producto_solicitado=s.producto_solicitado,
            alternativa=s.alternativa, motivo=s.motivo, responsable_id=s.responsable_id,
            estado=s.estado.value, fecha=s.fecha)

    def _a_dominio(self, f) -> SustitucionDeVenta:
        return SustitucionDeVenta(f.id, f.venta_id, f.producto_solicitado, f.motivo,
                                  f.responsable_id, f.fecha, EstadoSustitucion(f.estado),
                                  f.alternativa)


class SqlRetiroRepo(_SqlRepo):
    modelo = m.RetiroRow

    def _a_fila(self, r: RetiroDeLote):
        return m.RetiroRow(
            id=r.id, lote_id=r.lote_id, producto_id=r.producto_id, motivo=r.motivo,
            registrado_por=r.registrado_por, estado=r.estado.value,
            en_transito_pendiente=r.en_transito_pendiente,
            ejecuciones=[m.EjecucionRow(orden=i, sucursal_id=e.sucursal_id,
                                        identificadas=e.identificadas, retiradas=e.retiradas,
                                        responsable_id=e.responsable_id, fecha=e.fecha)
                         for i, e in enumerate(r.ejecuciones)])

    def _a_dominio(self, f) -> RetiroDeLote:
        ejecuciones = [EjecucionEnSucursal(e.sucursal_id, e.identificadas, e.retiradas,
                                           e.responsable_id, e.fecha) for e in f.ejecuciones]
        return RetiroDeLote(f.id, f.lote_id, f.producto_id, f.motivo, f.registrado_por,
                            EstadoRetiro(f.estado), ejecuciones, f.en_transito_pendiente)


class SqlDiferenciaRepo(_SqlRepo):
    modelo = m.DiferenciaRow

    def _a_fila(self, d: DiferenciaDeInventario):
        return m.DiferenciaRow(
            id=d.id, producto_id=d.producto_id, sucursal_id=d.sucursal_id, lote_id=d.lote_id,
            cantidad_registrada=d.cantidad_registrada, cantidad_fisica=d.cantidad_fisica,
            fecha_conteo=d.fecha_conteo, usuario_responsable=d.usuario_responsable,
            prioritaria=d.prioritaria, estado=d.estado.value,
            causa_identificada=d.causa_identificada, evidencia=d.evidencia,
            investigador_id=d.investigador_id)

    def _a_dominio(self, f) -> DiferenciaDeInventario:
        return DiferenciaDeInventario(
            f.id, f.producto_id, f.sucursal_id, f.cantidad_registrada, f.cantidad_fisica,
            f.fecha_conteo, f.usuario_responsable, f.lote_id, f.prioritaria,
            EstadoInvestigacion(f.estado), f.causa_identificada, f.evidencia, f.investigador_id)


class SqlAjusteRepo(_SqlRepo):
    modelo = m.AjusteRow

    def _a_fila(self, a: AjusteDeInventario):
        producto_id, lote_id, sucursal_id = a.clave_existencia
        return m.AjusteRow(
            id=a.id, diferencia_id=a.diferencia_id, producto_id=producto_id, lote_id=lote_id,
            sucursal_id=sucursal_id, cantidad_anterior=a.cantidad_anterior,
            cantidad_nueva=a.cantidad_nueva, motivo=a.motivo, evidencia=a.evidencia,
            ejecutor_id=a.ejecutor_id, fecha=a.fecha, estado=a.estado.value,
            autorizador_id=a.autorizador_id)

    def _a_dominio(self, f) -> AjusteDeInventario:
        return AjusteDeInventario(
            f.id, f.diferencia_id, (f.producto_id, f.lote_id, f.sucursal_id),
            f.cantidad_anterior, f.cantidad_nueva, f.motivo, f.evidencia, f.ejecutor_id,
            f.fecha, EstadoAjuste(f.estado), f.autorizador_id)


class SqlSolicitudRepo(_SqlRepo):
    modelo = m.SolicitudRow

    def _a_fila(self, s: SolicitudDeCompra):
        return m.SolicitudRow(
            id=s.id, sucursal_id=s.sucursal_id, estado=s.estado.value,
            solicitante_id=s.solicitante_id, fecha_envio=s.fecha_envio,
            necesidades=[m.NecesidadRow(
                id=n.id, orden=i, producto_id=n.producto_id, sucursal_id=n.sucursal_id,
                cantidad_requerida=n.cantidad_requerida, motivo=n.motivo.value,
                registrada_por=n.registrada_por, fecha=n.fecha, estado=n.estado.value,
                cantidad_confirmada=n.cantidad_confirmada, revisada_por=n.revisada_por)
                for i, n in enumerate(s.necesidades)])

    def _a_dominio(self, f) -> SolicitudDeCompra:
        necesidades = [NecesidadReposicion(
            n.id, n.producto_id, n.sucursal_id, n.cantidad_requerida, MotivoNecesidad(n.motivo),
            n.registrada_por, n.fecha, EstadoNecesidad(n.estado), n.cantidad_confirmada,
            n.revisada_por) for n in f.necesidades]
        return SolicitudDeCompra(f.id, f.sucursal_id, EstadoSolicitud(f.estado), necesidades,
                                 f.solicitante_id, f.fecha_envio)


class SqlAuditoria:
    def __init__(self, session: Session):
        self._s = session

    def registrar(self, usuario, accion, entidad, entidad_id, antes, despues) -> None:
        self._s.add(m.HistorialRow(usuario=usuario, accion=accion, entidad=entidad,
                                   entidad_id=entidad_id, antes=antes, despues=despues,
                                   fecha=datetime.now(timezone.utc)))

    def listar(self) -> list[RegistroAuditoria]:
        filas = self._s.scalars(select(m.HistorialRow).order_by(m.HistorialRow.id))
        return [RegistroAuditoria(f.usuario, f.accion, f.entidad, f.entidad_id, f.antes,
                                  f.despues, f.fecha) for f in filas]
