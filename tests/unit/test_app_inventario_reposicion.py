import pytest

from src.domain.errors import (
    InvalidTransition,
    NoEncontrado,
    PermisoDenegado,
    ReglaDeNegocioViolada,
)
from src.domain.retiro import EstadoRetiro
from src.domain.solicitud_compra import EstadoSolicitud, MotivoNecesidad
from src.domain.value_objects import Rol

RF = Rol.RESPONSABLE_FARMACIA


# --- Retiro ---
def test_retiro_completo(ctx):
    r = ctx.inventario.registrar_retiro("L1", "alerta sanitaria", "RF1", RF, "R1")
    assert ctx.store.lotes["L1"].retirado and r.estado is EstadoRetiro.REGISTRADO
    ctx.inventario.registrar_ejecucion_retiro("R1", "S1", 10, 10, "A1")
    ctx.inventario.concluir_retiro("R1", "A1")
    assert ctx.store.retiros["R1"].estado is EstadoRetiro.EJECUTADO
    assert [e.nombre for e in ctx.bus.publicados] == ["LoteRetirado", "RetiroDeLoteEjecutado"]


def test_retiro_solo_responsable_y_rollback(ctx):
    with pytest.raises(PermisoDenegado):
        ctx.inventario.registrar_retiro("L1", "m", "A1", Rol.ALMACEN)
    assert not ctx.store.lotes["L1"].retirado
    with pytest.raises(NoEncontrado):
        ctx.inventario.registrar_retiro("NOPE", "m", "RF1", RF)


# --- Diferencia -> Ajuste ---
def _dif_investigada(ctx):
    ctx.inventario.registrar_diferencia("S1", "P1", "L1", 7, "A1", diferencia_id="D1")
    ctx.inventario.investigar_diferencia("D1", "RF1", "error de captura", "conteo ciego")


def test_diferencia_no_modifica_existencia(ctx):
    d = ctx.inventario.registrar_diferencia("S1", "P1", "L1", 7, "A1")
    assert d.delta == -3 and ctx.store.existencias[("P1", "L1", "S1")].cantidad == 10


def test_diferencia_sin_existencia_o_igual(ctx):
    with pytest.raises(NoEncontrado):
        ctx.inventario.registrar_diferencia("S9", "P1", "L1", 1, "A1")
    with pytest.raises(ReglaDeNegocioViolada):
        ctx.inventario.registrar_diferencia("S1", "P1", "L1", 10, "A1")


def test_ajuste_flujo_completo(ctx):
    _dif_investigada(ctx)
    ctx.inventario.solicitar_ajuste("D1", "A1", "corrección", "J1")
    assert ctx.store.existencias[("P1", "L1", "S1")].cantidad == 10  # aún sin cambiar
    ctx.inventario.autorizar_ajuste("J1", "RF1", RF)
    ctx.inventario.aplicar_ajuste("J1", "RF1")
    assert ctx.store.existencias[("P1", "L1", "S1")].cantidad == 7
    nombres = [e.nombre for e in ctx.bus.publicados]
    assert "AjusteDeInventarioAplicado" in nombres


def test_almacen_no_autoriza_su_propio_ajuste(ctx):
    _dif_investigada(ctx)
    ctx.inventario.solicitar_ajuste("D1", "A1", "corrección", "J1")
    with pytest.raises(PermisoDenegado):
        ctx.inventario.autorizar_ajuste("J1", "A1", Rol.ALMACEN)
    with pytest.raises(PermisoDenegado):
        ctx.inventario.autorizar_ajuste("J1", "A1", RF)  # mismo usuario ejecutor
    with pytest.raises(InvalidTransition):
        ctx.inventario.aplicar_ajuste("J1", "A1")  # sin autorización no se aplica
    assert ctx.store.existencias[("P1", "L1", "S1")].cantidad == 10


def test_ajuste_requiere_investigacion_y_rechazo(ctx):
    ctx.inventario.registrar_diferencia("S1", "P1", "L1", 7, "A1", diferencia_id="D1")
    with pytest.raises(ReglaDeNegocioViolada):
        ctx.inventario.solicitar_ajuste("D1", "A1", "m")
    ctx.inventario.investigar_diferencia("D1", "RF1", "error", "conteo")
    ctx.inventario.solicitar_ajuste("D1", "A1", "m", "J1")
    ctx.inventario.rechazar_ajuste("J1", "RF1", RF)
    with pytest.raises(InvalidTransition):
        ctx.inventario.aplicar_ajuste("J1", "RF1")


# --- Consulta entre sucursales ---
def test_consulta_existencias_informativa(ctx):
    r = ctx.inventario.consultar_existencias("P1")
    por_suc = {(e.sucursal_id, e.lote_id): e for e in r}
    assert por_suc[("S2", "L1")].cantidad == 4 and por_suc[("S2", "L1")].clasificacion == "NORMAL"
    assert por_suc[("S1", "LC")].clasificacion == "CADUCADO"
    with pytest.raises(NoEncontrado):
        ctx.inventario.consultar_existencias("PX")
    assert ctx.store.existencias[("P1", "L1", "S2")].cantidad == 4  # sin reserva (RN-03)


# --- Reposición ---
def test_reposicion_flujo_y_permisos(ctx):
    ctx.reposicion.crear_solicitud("S1", "A1", "SC1")
    ctx.reposicion.registrar_necesidad("SC1", "P1", 5, MotivoNecesidad.FALTANTE, "A1", "N1")
    ctx.reposicion.registrar_necesidad("SC1", "P2", 3, MotivoNecesidad.EXISTENCIA_BAJA, "A1", "N2")
    with pytest.raises(PermisoDenegado):
        ctx.reposicion.confirmar_necesidad("SC1", "N1", "A1", Rol.ALMACEN)
    ctx.reposicion.confirmar_necesidad("SC1", "N1", "RF1", RF)
    ctx.reposicion.rechazar_necesidad("SC1", "N2", "RF1", RF)
    s = ctx.reposicion.enviar_solicitud("SC1", "RF1", RF)
    assert s.estado is EstadoSolicitud.ENVIADA and s.lineas == [("P1", 5)]
    assert ctx.store.solicitudes["SC1"].estado is EstadoSolicitud.ENVIADA
    assert ctx.bus.publicados[-1].nombre == "SolicitudDeCompraEnviada"


def test_reposicion_errores(ctx):
    ctx.reposicion.crear_solicitud("S1", "A1", "SC1")
    with pytest.raises(NoEncontrado):
        ctx.reposicion.registrar_necesidad("SC1", "PX", 1, MotivoNecesidad.FALTANTE, "A1")
    with pytest.raises(NoEncontrado):
        ctx.reposicion.enviar_solicitud("NOPE", "RF1", RF)
    with pytest.raises(ReglaDeNegocioViolada):
        ctx.reposicion.enviar_solicitud("SC1", "RF1", RF)  # sin necesidades confirmadas
