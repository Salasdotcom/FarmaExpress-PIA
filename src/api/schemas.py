"""Contratos de entrada/salida de la API (aparecen en Swagger/OpenAPI)."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.application.inventario_service import CaducidadConsultada, ExistenciaConsultada
from src.domain.ajuste import AjusteDeInventario
from src.domain.auditoria import RegistroAuditoria
from src.domain.diferencia import DiferenciaDeInventario
from src.domain.retiro import RetiroDeLote
from src.domain.solicitud_compra import SolicitudDeCompra
from src.domain.value_objects import ResultadoRevision
from src.domain.venta import Venta


# ----------------------------- entrada -----------------------------
class ItemIn(BaseModel):
    producto_id: str
    cantidad: int
    lote_id: Optional[str] = None


class VentaIn(BaseModel):
    sucursal_id: str
    items: list[ItemIn] = Field(default_factory=list)


class CancelarIn(BaseModel):
    motivo: str = ""


class RecetaIn(BaseModel):
    folio: str
    medico: str
    cedula_medico: str
    nombre_paciente: str
    fecha_emision: date
    resultado: ResultadoRevision


class RetiroIn(BaseModel):
    motivo: str


class EjecucionIn(BaseModel):
    sucursal_id: str
    identificadas: int
    retiradas: int


class DiferenciaIn(BaseModel):
    sucursal_id: str
    producto_id: str
    lote_id: Optional[str] = None
    cantidad_fisica: int
    prioritaria: bool = False


class InvestigacionIn(BaseModel):
    causa: str = ""
    evidencia: str = ""


class AjusteIn(BaseModel):
    diferencia_id: str
    motivo: str


class SolicitudIn(BaseModel):
    sucursal_id: str


class NecesidadIn(BaseModel):
    producto_id: str
    cantidad: int
    motivo: str = Field(description="FALTANTE | EXISTENCIA_BAJA | CADUCADO")


class ConfirmarIn(BaseModel):
    cantidad: Optional[int] = None


# ------------------------------ salida ------------------------------
class LineaOut(BaseModel):
    producto_id: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    lote_id: Optional[str]
    requiere_receta: bool


class RecetaOut(BaseModel):
    folio: str
    medico: str
    nombre_paciente: str
    fecha_emision: date
    resultado: Optional[str]
    revisada_por: Optional[str]


class VentaOut(BaseModel):
    id: str
    sucursal_id: str
    cajero_id: str
    estado: str
    lineas: list[LineaOut]
    total: Decimal
    moneda: str = "MXN"
    requiere_receta: bool
    receta: Optional[RecetaOut]
    observaciones: str


class CaducidadOut(BaseModel):
    lote_id: str
    producto_id: str
    fecha_caducidad: date
    dias_restantes: int
    clasificacion: str
    retirado: bool
    vendible: bool


class ExistenciaOut(BaseModel):
    sucursal_id: str
    lote_id: Optional[str]
    cantidad: int
    clasificacion: Optional[str]
    retirado: bool


class ExistenciasOut(BaseModel):
    producto_id: str
    informativo: bool = True
    nota: str = "Consulta informativa: sin reserva ni transferencia (RN-03)"
    existencias: list[ExistenciaOut]


class EjecucionOut(BaseModel):
    sucursal_id: str
    identificadas: int
    retiradas: int
    responsable_id: str


class RetiroOut(BaseModel):
    id: str
    lote_id: str
    producto_id: str
    motivo: str
    estado: str
    en_transito_pendiente: int
    total_identificadas: int
    total_retiradas: int
    ejecuciones: list[EjecucionOut]


class DiferenciaOut(BaseModel):
    id: str
    producto_id: str
    sucursal_id: str
    lote_id: Optional[str]
    cantidad_registrada: int
    cantidad_fisica: int
    delta: int
    prioritaria: bool
    estado: str
    causa_identificada: str
    evidencia: str
    ajustable: bool


class AjusteOut(BaseModel):
    id: str
    diferencia_id: str
    cantidad_anterior: int
    cantidad_nueva: int
    motivo: str
    estado: str
    ejecutor_id: str
    autorizador_id: Optional[str]


class NecesidadOut(BaseModel):
    id: str
    producto_id: str
    cantidad_requerida: int
    motivo: str
    estado: str
    cantidad_confirmada: Optional[int]


class SolicitudOut(BaseModel):
    id: str
    sucursal_id: str
    estado: str
    solicitante_id: Optional[str]
    necesidades: list[NecesidadOut]
    lineas_a_comprar: list[dict]


class AuditoriaOut(BaseModel):
    usuario: str
    accion: str
    entidad: str
    entidad_id: str
    antes: str
    despues: str
    fecha: datetime


# ------------------------- conversión dominio -> salida -------------------------
def venta_out(v: Venta) -> VentaOut:
    r = v.receta
    return VentaOut(
        id=v.id, sucursal_id=v.sucursal_id, cajero_id=v.cajero_id, estado=v.estado.value,
        lineas=[LineaOut(producto_id=li.producto_id, cantidad=li.cantidad,
                         precio_unitario=li.precio_unitario.monto, subtotal=li.subtotal.monto,
                         lote_id=li.lote_id, requiere_receta=li.requiere_receta)
                for li in v.lineas],
        total=v.total.monto, requiere_receta=v.requiere_receta,
        receta=None if r is None else RecetaOut(
            folio=r.folio, medico=r.medico, nombre_paciente=r.nombre_paciente,
            fecha_emision=r.fecha_emision, resultado=r.resultado.value if r.resultado else None,
            revisada_por=r.revisada_por),
        observaciones=v.observaciones)


def caducidad_out(c: CaducidadConsultada) -> CaducidadOut:
    return CaducidadOut(lote_id=c.lote_id, producto_id=c.producto_id,
                        fecha_caducidad=c.fecha_caducidad, dias_restantes=c.dias_restantes,
                        clasificacion=c.clasificacion, retirado=c.retirado, vendible=c.vendible)


def existencias_out(producto_id: str, items: list[ExistenciaConsultada]) -> ExistenciasOut:
    return ExistenciasOut(producto_id=producto_id, existencias=[
        ExistenciaOut(sucursal_id=e.sucursal_id, lote_id=e.lote_id, cantidad=e.cantidad,
                      clasificacion=e.clasificacion, retirado=e.retirado) for e in items])


def retiro_out(r: RetiroDeLote) -> RetiroOut:
    return RetiroOut(
        id=r.id, lote_id=r.lote_id, producto_id=r.producto_id, motivo=r.motivo,
        estado=r.estado.value, en_transito_pendiente=r.en_transito_pendiente,
        total_identificadas=r.total_identificadas, total_retiradas=r.total_retiradas,
        ejecuciones=[EjecucionOut(sucursal_id=e.sucursal_id, identificadas=e.identificadas,
                                  retiradas=e.retiradas, responsable_id=e.responsable_id)
                     for e in r.ejecuciones])


def diferencia_out(d: DiferenciaDeInventario) -> DiferenciaOut:
    return DiferenciaOut(
        id=d.id, producto_id=d.producto_id, sucursal_id=d.sucursal_id, lote_id=d.lote_id,
        cantidad_registrada=d.cantidad_registrada, cantidad_fisica=d.cantidad_fisica,
        delta=d.delta, prioritaria=d.prioritaria, estado=d.estado.value,
        causa_identificada=d.causa_identificada, evidencia=d.evidencia, ajustable=d.ajustable)


def ajuste_out(a: AjusteDeInventario) -> AjusteOut:
    return AjusteOut(id=a.id, diferencia_id=a.diferencia_id,
                     cantidad_anterior=a.cantidad_anterior, cantidad_nueva=a.cantidad_nueva,
                     motivo=a.motivo, estado=a.estado.value, ejecutor_id=a.ejecutor_id,
                     autorizador_id=a.autorizador_id)


def solicitud_out(s: SolicitudDeCompra) -> SolicitudOut:
    return SolicitudOut(
        id=s.id, sucursal_id=s.sucursal_id, estado=s.estado.value,
        solicitante_id=s.solicitante_id,
        necesidades=[NecesidadOut(id=n.id, producto_id=n.producto_id,
                                  cantidad_requerida=n.cantidad_requerida, motivo=n.motivo.value,
                                  estado=n.estado.value, cantidad_confirmada=n.cantidad_confirmada)
                     for n in s.necesidades],
        lineas_a_comprar=[{"producto_id": p, "cantidad": c} for p, c in s.lineas])


def auditoria_out(r: RegistroAuditoria) -> AuditoriaOut:
    return AuditoriaOut(usuario=r.usuario, accion=r.accion, entidad=r.entidad,
                        entidad_id=r.entidad_id, antes=r.antes, despues=r.despues, fecha=r.fecha)
