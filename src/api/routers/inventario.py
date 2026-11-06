from fastapi import APIRouter

from src.api import schemas as s
from src.api.deps import Autenticado, Cont, EnInventario, SoloRF

router = APIRouter(tags=["Inventario (US01, US03-US05, US15-US17)"])


# ----- consultas -----
@router.get("/lotes/{lote_id}/caducidad", response_model=s.CaducidadOut,
            summary="Clasificación de caducidad de un lote (US01, RN-01)")
def caducidad(lote_id: str, c: Cont, u: Autenticado):
    return s.caducidad_out(c.inventario.consultar_caducidad(lote_id))


@router.get("/existencias/{producto_id}", response_model=s.ExistenciasOut,
            summary="Existencias por sucursal y lote (US05, informativa)")
def existencias(producto_id: str, c: Cont, u: Autenticado):
    return s.existencias_out(producto_id, c.inventario.consultar_existencias(producto_id))


# ----- retiro de lote -----
@router.post("/lotes/{lote_id}/retiro", response_model=s.RetiroOut, status_code=201,
             summary="Registrar retiro confirmado: bloquea el lote en todas las sucursales")
def registrar_retiro(lote_id: str, datos: s.RetiroIn, c: Cont, u: SoloRF):
    return s.retiro_out(c.inventario.registrar_retiro(lote_id, datos.motivo, u.id, u.rol))


@router.get("/retiros/{retiro_id}", response_model=s.RetiroOut, summary="Consultar retiro")
def obtener_retiro(retiro_id: str, c: Cont, u: Autenticado):
    return s.retiro_out(c.inventario.obtener_retiro(retiro_id))


@router.post("/retiros/{retiro_id}/ejecuciones", response_model=s.RetiroOut, status_code=201,
             summary="Registrar unidades identificadas y retiradas en una sucursal")
def registrar_ejecucion(retiro_id: str, datos: s.EjecucionIn, c: Cont, u: EnInventario):
    return s.retiro_out(c.inventario.registrar_ejecucion_retiro(
        retiro_id, datos.sucursal_id, datos.identificadas, datos.retiradas, u.id))


@router.post("/retiros/{retiro_id}/concluir", response_model=s.RetiroOut,
             summary="Concluir el retiro (RN-02: sin unidades en tránsito pendientes)")
def concluir_retiro(retiro_id: str, c: Cont, u: EnInventario):
    return s.retiro_out(c.inventario.concluir_retiro(retiro_id, u.id))


# ----- diferencias -----
@router.post("/diferencias", response_model=s.DiferenciaOut, status_code=201,
             summary="Registrar diferencia entre conteo físico y existencia registrada")
def registrar_diferencia(datos: s.DiferenciaIn, c: Cont, u: EnInventario):
    return s.diferencia_out(c.inventario.registrar_diferencia(
        datos.sucursal_id, datos.producto_id, datos.lote_id, datos.cantidad_fisica, u.id,
        datos.prioritaria))


@router.get("/diferencias/{diferencia_id}", response_model=s.DiferenciaOut,
            summary="Consultar diferencia")
def obtener_diferencia(diferencia_id: str, c: Cont, u: Autenticado):
    return s.diferencia_out(c.inventario.obtener_diferencia(diferencia_id))


@router.post("/diferencias/{diferencia_id}/investigacion", response_model=s.DiferenciaOut,
             summary="Registrar causa y evidencia, o dejarla pendiente de aclaración (US16)")
def investigar(diferencia_id: str, datos: s.InvestigacionIn, c: Cont, u: EnInventario):
    return s.diferencia_out(c.inventario.investigar_diferencia(
        diferencia_id, u.id, datos.causa, datos.evidencia))


# ----- ajustes (el dominio impide que quien ejecuta autorice, RN-09) -----
@router.post("/ajustes", response_model=s.AjusteOut, status_code=201,
             summary="Solicitar ajuste a partir de una diferencia investigada")
def solicitar_ajuste(datos: s.AjusteIn, c: Cont, u: EnInventario):
    return s.ajuste_out(c.inventario.solicitar_ajuste(datos.diferencia_id, u.id, datos.motivo))


@router.get("/ajustes/{ajuste_id}", response_model=s.AjusteOut, summary="Consultar ajuste")
def obtener_ajuste(ajuste_id: str, c: Cont, u: Autenticado):
    return s.ajuste_out(c.inventario.obtener_ajuste(ajuste_id))


@router.post("/ajustes/{ajuste_id}/autorizar", response_model=s.AjusteOut,
             summary="Autorizar ajuste (responsable de farmacia distinto del ejecutor)")
def autorizar_ajuste(ajuste_id: str, c: Cont, u: Autenticado):
    return s.ajuste_out(c.inventario.autorizar_ajuste(ajuste_id, u.id, u.rol))


@router.post("/ajustes/{ajuste_id}/rechazar", response_model=s.AjusteOut, summary="Rechazar ajuste")
def rechazar_ajuste(ajuste_id: str, c: Cont, u: Autenticado):
    return s.ajuste_out(c.inventario.rechazar_ajuste(ajuste_id, u.id, u.rol))


@router.post("/ajustes/{ajuste_id}/aplicar", response_model=s.AjusteOut,
             summary="Aplicar un ajuste AUTORIZADO: es lo único que modifica la existencia")
def aplicar_ajuste(ajuste_id: str, c: Cont, u: EnInventario):
    return s.ajuste_out(c.inventario.aplicar_ajuste(ajuste_id, u.id))
