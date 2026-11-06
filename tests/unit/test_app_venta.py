from datetime import date

import pytest

from src.application.venta_service import ItemVenta
from src.domain.errors import (
    InvalidTransition,
    NoEncontrado,
    PermisoDenegado,
    ReglaDeNegocioViolada,
    ValidacionDeVentaFallida,
)
from src.domain.value_objects import EstadoVenta, ResultadoRevision, Rol
from src.domain.venta import Receta

RF = Rol.RESPONSABLE_FARMACIA


def receta():
    return Receta("R1", "Dr. X", "123", "Paciente", date(2026, 11, 1))


def test_ds01_completar_descuenta_existencia_audita_y_publica(ctx):
    v = ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 3, "L1")], "V1")
    ctx.ventas.completar_venta(v.id, "C1")
    assert ctx.store.ventas["V1"].estado is EstadoVenta.COMPLETADA
    assert ctx.store.existencias[("P1", "L1", "S1")].cantidad == 7
    assert [e.nombre for e in ctx.bus.publicados] == ["VentaCompletada"]
    assert [h.accion for h in ctx.store.historial] == ["CREAR_VENTA", "COMPLETAR_VENTA"]


def test_ds02_caducado_bloquea_y_no_cambia_nada(ctx):
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 1, "LC")], "V1")
    with pytest.raises(ValidacionDeVentaFallida) as e:
        ctx.ventas.completar_venta("V1", "C1")
    assert "MEDICAMENTO_CADUCADO" in e.value.violaciones
    assert ctx.store.ventas["V1"].estado is EstadoVenta.EN_PROCESO
    assert ctx.store.existencias[("P1", "LC", "S1")].cantidad == 5
    assert ctx.bus.publicados == []


def test_lote_retirado_bloquea_en_otra_sucursal(ctx):
    ctx.inventario.registrar_retiro("L1", "alerta", "RF1", RF)
    ctx.ventas.crear_venta("S2", "C1", [ItemVenta("P1", 1, "L1")], "V2")
    with pytest.raises(ValidacionDeVentaFallida) as e:
        ctx.ventas.completar_venta("V2", "C1")
    assert "LOTE_RETIRADO" in e.value.violaciones


def test_existencia_insuficiente(ctx):
    ctx.ventas.crear_venta("S2", "C1", [ItemVenta("P1", 5, "L1")], "V1")  # S2 tiene 4
    with pytest.raises(ValidacionDeVentaFallida) as e:
        ctx.ventas.completar_venta("V1", "C1")
    assert "EXISTENCIA_INSUFICIENTE" in e.value.violaciones


def test_receta_flujo_completo_y_bloqueo(ctx):
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P2", 1, "L2")], "V1")
    with pytest.raises(ValidacionDeVentaFallida):
        ctx.ventas.completar_venta("V1", "C1")  # sin receta revisada
    ctx.ventas.revisar_receta("V1", receta(), ResultadoRevision.INCOMPLETA, "RF1", RF)
    with pytest.raises(ValidacionDeVentaFallida):
        ctx.ventas.completar_venta("V1", "C1")
    ctx.ventas.revisar_receta("V1", receta(), ResultadoRevision.ACEPTADA, "RF1", RF)
    assert ctx.ventas.completar_venta("V1", "C1").estado is EstadoVenta.COMPLETADA


def test_revisar_receta_solo_responsable(ctx):
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P2", 1, "L2")], "V1")
    with pytest.raises(PermisoDenegado):
        ctx.ventas.revisar_receta("V1", receta(), ResultadoRevision.ACEPTADA, "C1", Rol.CAJERO)


def test_completar_venta_ya_completada_o_cancelada_es_409(ctx):
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 1, "L1")], "V1")
    ctx.ventas.completar_venta("V1", "C1")
    with pytest.raises(InvalidTransition):
        ctx.ventas.completar_venta("V1", "C1")
    assert ctx.store.existencias[("P1", "L1", "S1")].cantidad == 9  # no se descuenta dos veces
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 1, "L1")], "V2")
    ctx.ventas.cancelar_venta("V2", "C1", "cliente se fue")
    with pytest.raises(InvalidTransition):
        ctx.ventas.completar_venta("V2", "C1")


def test_cancelar_publica_evento(ctx):
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 1, "L1")], "V1")
    ctx.ventas.cancelar_venta("V1", "C1")
    assert ctx.bus.publicados[-1].nombre == "VentaCancelada"


def test_crear_venta_validaciones(ctx):
    with pytest.raises(NoEncontrado):
        ctx.ventas.crear_venta("S1", "C1", [ItemVenta("PX", 1)])
    with pytest.raises(NoEncontrado):
        ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 1, "LX")])
    with pytest.raises(ReglaDeNegocioViolada):
        ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P3", 1)])      # deshabilitado
    with pytest.raises(ReglaDeNegocioViolada):
        ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 0, "L1")])  # cantidad 0
    assert ctx.store.ventas == {}  # rollback: no quedó venta a medias


def test_agregar_linea_y_obtener(ctx):
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 1, "L1")], "V1")
    v = ctx.ventas.agregar_linea("V1", ItemVenta("P1", 2, "L1"), "C1")
    assert len(v.lineas) == 2 and ctx.ventas.obtener_venta("V1").total.monto == 150
    with pytest.raises(NoEncontrado):
        ctx.ventas.obtener_venta("NOPE")


def test_rollback_si_falla_a_mitad(ctx):
    """Una excepción inesperada después de modificar la existencia deja todo intacto."""
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 3, "L1")], "V1")
    original = ctx.store.ventas["V1"].completar

    def falla():
        raise RuntimeError("fallo simulado")

    ctx.store.ventas["V1"].completar = falla
    with pytest.raises(RuntimeError):
        ctx.ventas.completar_venta("V1", "C1")
    ctx.store.ventas["V1"].completar = original
    assert ctx.store.existencias[("P1", "L1", "S1")].cantidad == 10
    assert ctx.store.ventas["V1"].estado is EstadoVenta.EN_PROCESO
