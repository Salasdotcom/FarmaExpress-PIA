from typing import Annotated

from fastapi import APIRouter, Form

from src.api import schemas as s
from src.api.deps import Autenticado, Cont, EnInventario, SoloRF

router = APIRouter(tags=["Inventario (US01, US03-US05, US15-US17)"])


# ----- consultas -----
@router.get("/lotes/{lote_id}/caducidad", response_model=s.CaducidadOut,
            summary="Clasificación de caducidad de un lote (US01, RN-01)")
def caducidad(lote_id: str, c: Cont, u: Autenticado):
    r = s.caducidad_out(c.inventario.consultar_caducidad(lote_id))
    r.mensaje = (f"El lote {r.lote_id} está {r.clasificacion} (faltan {r.dias_restantes} días) y "
                 + ("SÍ se puede vender." if r.vendible else "NO se puede vender."))
    return r


@router.get("/existencias/{producto_id}", response_model=s.ExistenciasOut,
            summary="Existencias por sucursal y lote (US05, informativa)")
def existencias(producto_id: str, c: Cont, u: Autenticado):
    r = s.existencias_out(producto_id, c.inventario.consultar_existencias(producto_id))
    r.mensaje = (f"{producto_id} tiene {sum(e.cantidad for e in r.existencias)} pieza(s) "
                 f"en {len(r.existencias)} registro(s) de sucursal/lote.")
    return r


# ----- retiro de lote -----
@router.post("/lotes/{lote_id}/retiro", response_model=s.RetiroOut, status_code=201,
             summary="Registrar retiro confirmado: bloquea el lote en todas las sucursales")
def registrar_retiro(lote_id: str, datos: Annotated[s.RetiroIn, Form()], c: Cont, u: SoloRF):
    r = s.retiro_out(c.inventario.registrar_retiro(lote_id, datos.motivo, u.id, u.rol))
    r.mensaje = (f"Retiro {r.id} registrado: el lote {r.lote_id} queda bloqueado para la venta "
                 "en todas las sucursales.")
    return r


@router.get("/retiros/{retiro_id}", response_model=s.RetiroOut, summary="Consultar retiro")
def obtener_retiro(retiro_id: str, c: Cont, u: Autenticado):
    r = s.retiro_out(c.inventario.obtener_retiro(retiro_id))
    r.mensaje = f"El retiro {r.id} está {r.estado}."
    return r


@router.post("/retiros/{retiro_id}/ejecuciones", response_model=s.RetiroOut, status_code=201,
             summary="Registrar unidades identificadas y retiradas en una sucursal")
def registrar_ejecucion(retiro_id: str, datos: Annotated[s.EjecucionIn, Form()], c: Cont,
                        u: EnInventario):
    r = s.retiro_out(c.inventario.registrar_ejecucion_retiro(
        retiro_id, datos.sucursal_id, datos.identificadas, datos.retiradas, u.id))
    r.mensaje = (f"Se registraron {datos.retiradas} de {datos.identificadas} unidades retiradas "
                 f"en {datos.sucursal_id}. Pendientes en tránsito: {r.en_transito_pendiente}.")
    return r


@router.post("/retiros/{retiro_id}/concluir", response_model=s.RetiroOut,
             summary="Concluir el retiro (RN-02: sin unidades en tránsito pendientes)")
def concluir_retiro(retiro_id: str, c: Cont, u: EnInventario):
    r = s.retiro_out(c.inventario.concluir_retiro(retiro_id, u.id))
    r.mensaje = f"Retiro {r.id} concluido: no quedan unidades en tránsito pendientes."
    return r


# ----- diferencias -----
@router.post("/diferencias", response_model=s.DiferenciaOut, status_code=201,
             summary="Registrar diferencia entre conteo físico y existencia registrada")
def registrar_diferencia(datos: Annotated[s.DiferenciaIn, Form()], c: Cont, u: EnInventario):
    d = s.diferencia_out(c.inventario.registrar_diferencia(
        datos.sucursal_id, datos.producto_id, datos.lote_id or None, datos.cantidad_fisica, u.id,
        datos.prioritaria))
    d.mensaje = (f"Diferencia {d.id} registrada: sistema {d.cantidad_registrada}, físico "
                 f"{d.cantidad_fisica} (delta {d.delta}). El inventario NO se modificó; "
                 "falta investigar y solicitar un ajuste.")
    return d


@router.get("/diferencias/{diferencia_id}", response_model=s.DiferenciaOut,
            summary="Consultar diferencia")
def obtener_diferencia(diferencia_id: str, c: Cont, u: Autenticado):
    d = s.diferencia_out(c.inventario.obtener_diferencia(diferencia_id))
    d.mensaje = f"La diferencia {d.id} está {d.estado}."
    return d


@router.post("/diferencias/{diferencia_id}/investigacion", response_model=s.DiferenciaOut,
             summary="Registrar causa y evidencia, o dejarla pendiente de aclaración (US16)")
def investigar(diferencia_id: str, datos: Annotated[s.InvestigacionIn, Form()], c: Cont,
              u: EnInventario):
    d = s.diferencia_out(c.inventario.investigar_diferencia(
        diferencia_id, u.id, datos.causa, datos.evidencia))
    d.mensaje = (f"Investigación registrada; la diferencia {d.id} quedó {d.estado}."
                 + (" Ya puede solicitarse un ajuste." if d.ajustable else
                    " Aún no es ajustable (falta causa y evidencia)."))
    return d


# ----- ajustes (el dominio impide que quien ejecuta autorice, RN-09) -----
@router.post("/ajustes", response_model=s.AjusteOut, status_code=201,
             summary="Solicitar ajuste a partir de una diferencia investigada")
def solicitar_ajuste(datos: Annotated[s.AjusteIn, Form()], c: Cont, u: EnInventario):
    a = s.ajuste_out(c.inventario.solicitar_ajuste(datos.diferencia_id, u.id, datos.motivo))
    a.mensaje = (f"Ajuste {a.id} solicitado ({a.cantidad_anterior} → {a.cantidad_nueva}). "
                 "Requiere autorización de un responsable de farmacia distinto del solicitante.")
    return a


@router.get("/ajustes/{ajuste_id}", response_model=s.AjusteOut, summary="Consultar ajuste")
def obtener_ajuste(ajuste_id: str, c: Cont, u: Autenticado):
    a = s.ajuste_out(c.inventario.obtener_ajuste(ajuste_id))
    a.mensaje = f"El ajuste {a.id} está {a.estado}."
    return a


@router.post("/ajustes/{ajuste_id}/autorizar", response_model=s.AjusteOut,
             summary="Autorizar ajuste (responsable de farmacia distinto del ejecutor)")
def autorizar_ajuste(ajuste_id: str, c: Cont, u: Autenticado):
    a = s.ajuste_out(c.inventario.autorizar_ajuste(ajuste_id, u.id, u.rol))
    a.mensaje = (f"Ajuste {a.id} autorizado por {u.id}. "
                 "Falta aplicarlo para modificar la existencia.")
    return a


@router.post("/ajustes/{ajuste_id}/rechazar", response_model=s.AjusteOut, summary="Rechazar ajuste")
def rechazar_ajuste(ajuste_id: str, c: Cont, u: Autenticado):
    a = s.ajuste_out(c.inventario.rechazar_ajuste(ajuste_id, u.id, u.rol))
    a.mensaje = f"Ajuste {a.id} rechazado; la existencia no cambió."
    return a


@router.post("/ajustes/{ajuste_id}/aplicar", response_model=s.AjusteOut,
             summary="Aplicar un ajuste AUTORIZADO: es lo único que modifica la existencia")
def aplicar_ajuste(ajuste_id: str, c: Cont, u: EnInventario):
    a = s.ajuste_out(c.inventario.aplicar_ajuste(ajuste_id, u.id))
    a.mensaje = (f"Ajuste {a.id} aplicado: la existencia pasó de {a.cantidad_anterior} a "
                 f"{a.cantidad_nueva}.")
    return a
