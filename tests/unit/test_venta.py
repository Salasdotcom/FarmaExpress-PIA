from datetime import date
from decimal import Decimal

import pytest

from src.domain.errors import InvalidTransition, ReglaDeNegocioViolada
from src.domain.value_objects import Dinero, EstadoVenta, ResultadoRevision
from src.domain.venta import LineaDeVenta, Receta, Venta


def linea(cant=2, receta=False):
    return LineaDeVenta("P1", cant, Dinero(Decimal("50.00")), "L1", receta)


def receta():
    return Receta("R1", "Dr. X", "123", "Paciente", date(2026, 11, 1))


def venta():
    v = Venta("V1", "S1", "C1")
    v.agregar_linea(linea())
    return v


def test_total_decimal():
    assert venta().total.monto == Decimal("100.00")


def test_completar_emite_evento():
    v = venta()
    v.completar()
    assert v.estado is EstadoVenta.COMPLETADA
    assert [e.nombre for e in v.events] == ["VentaCompletada"]


def test_cancelar_en_proceso():
    v = venta()
    v.cancelar("abandono")
    assert v.estado is EstadoVenta.CANCELADA
    assert v.events[-1].nombre == "VentaCancelada"


def test_completar_sin_lineas_falla():
    with pytest.raises(ReglaDeNegocioViolada):
        Venta("V2", "S1", "C1").completar()


@pytest.mark.parametrize("primera,segunda", [
    ("completar", "completar"), ("completar", "cancelar"),
    ("cancelar", "completar"), ("cancelar", "cancelar"),
])
def test_transiciones_invalidas_no_agregan_eventos(primera, segunda):
    v = venta()
    getattr(v, primera)()
    n = len(v.events)
    with pytest.raises(InvalidTransition):
        getattr(v, segunda)()
    assert len(v.events) == n


def test_venta_completada_rechaza_cambios_economicos():
    v = venta()
    v.completar()
    with pytest.raises(InvalidTransition):
        v.agregar_linea(linea())
    with pytest.raises(InvalidTransition):
        v.quitar_linea(0)


def test_linea_cantidad_cero():
    with pytest.raises(ReglaDeNegocioViolada):
        linea(0)


def test_quitar_linea_en_proceso():
    v = venta()
    v.quitar_linea(0)
    assert v.lineas == []


def test_revision_receta():
    v = Venta("V3", "S1", "C1")
    v.agregar_linea(linea(receta=True))
    assert v.requiere_receta
    v.registrar_revision_receta(receta(), ResultadoRevision.ACEPTADA, "RF1")
    assert v.receta.revisada_por == "RF1"
    assert v.events[-1].nombre == "RecetaRevisada"


def test_revision_receta_sin_medicamento_con_receta():
    with pytest.raises(ReglaDeNegocioViolada):
        venta().registrar_revision_receta(receta(), ResultadoRevision.ACEPTADA, "RF1")


def test_correccion_descriptiva_conserva_historial():
    v = venta()
    v.completar()
    v.corregir_dato_descriptivo("observaciones", "nuevo", "typo", "C1", "RF1")
    assert v.observaciones == "nuevo"
    assert v.correcciones[0]["anterior"] == ""
    assert v.correcciones[0]["autorizador"] == "RF1"


def test_correccion_campo_economico_rechazada():
    v = venta()
    v.completar()
    with pytest.raises(ReglaDeNegocioViolada):
        v.corregir_dato_descriptivo("lineas", "x", "m", "C1", "RF1")


def test_correccion_sin_motivo_o_en_proceso():
    v = venta()
    with pytest.raises(InvalidTransition):
        v.corregir_dato_descriptivo("observaciones", "x", "m", "C1", "RF1")
    v.completar()
    with pytest.raises(ReglaDeNegocioViolada):
        v.corregir_dato_descriptivo("observaciones", "x", " ", "C1", "RF1")
