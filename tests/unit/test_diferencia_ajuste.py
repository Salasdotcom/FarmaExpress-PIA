import pytest

from src.domain.ajuste import AjusteDeInventario, EstadoAjuste
from src.domain.diferencia import DiferenciaDeInventario, EstadoInvestigacion
from src.domain.errors import InvalidTransition, PermisoDenegado, ReglaDeNegocioViolada
from src.domain.existencia import Existencia
from src.domain.value_objects import Rol


def dif(registrada=10, fisica=7, lote="L1"):
    return DiferenciaDeInventario.registrar("D1", "P1", "S1", registrada, fisica, "A1", lote)


def dif_investigada():
    d = dif()
    d.registrar_investigacion("RF1", causa="error de captura", evidencia="conteo ciego")
    return d


def ajuste():
    return AjusteDeInventario.solicitar("J1", dif_investigada(), "A1", "corrección por conteo")


# --- Diferencia (US15, US16) ---
def test_registrar_diferencia_y_evento():
    d = dif()
    assert d.delta == -3 and d.estado is EstadoInvestigacion.SIN_INVESTIGAR
    assert d.events[0].nombre == "DiferenciaDeInventarioRegistrada"
    assert d.clave_existencia == ("P1", "L1", "S1")


def test_diferencia_sin_diferencia_o_negativa_rechazada():
    with pytest.raises(ReglaDeNegocioViolada):
        dif(5, 5)
    with pytest.raises(ReglaDeNegocioViolada):
        dif(-1, 2)


def test_investigacion_causa_identificada():
    d = dif_investigada()
    assert d.estado is EstadoInvestigacion.CAUSA_IDENTIFICADA and d.ajustable
    assert d.events[-1].nombre == "InvestigacionDeInventarioConcluida"


def test_investigacion_pendiente_no_es_ajustable():
    d = dif()
    d.registrar_investigacion("RF1", causa="  ", evidencia="notas")
    assert d.estado is EstadoInvestigacion.PENDIENTE_ACLARACION and not d.ajustable


def test_causa_sin_evidencia_no_es_ajustable():
    d = dif()
    d.registrar_investigacion("RF1", causa="merma")
    assert not d.ajustable


# --- Ajuste (US17, RN-09, ADR-02) ---
def test_solicitar_requiere_diferencia_ajustable_y_motivo():
    with pytest.raises(ReglaDeNegocioViolada):
        AjusteDeInventario.solicitar("J", dif(), "A1", "m")
    with pytest.raises(ReglaDeNegocioViolada):
        AjusteDeInventario.solicitar("J", dif_investigada(), "A1", " ")


def test_ajuste_conserva_anterior_y_nueva():
    a = ajuste()
    assert (a.cantidad_anterior, a.cantidad_nueva) == (10, 7)
    assert a.estado is EstadoAjuste.PENDIENTE


def test_autorizar_por_responsable():
    a = ajuste()
    a.autorizar("RF1", Rol.RESPONSABLE_FARMACIA)
    assert a.estado is EstadoAjuste.AUTORIZADO and a.autorizador_id == "RF1"
    assert a.events[-1].nombre == "AjusteDeInventarioAutorizado"


def test_almacen_no_autoriza():
    with pytest.raises(PermisoDenegado):
        ajuste().autorizar("A2", Rol.ALMACEN)


def test_nadie_autoriza_su_propio_ajuste():
    with pytest.raises(PermisoDenegado):
        ajuste().autorizar("A1", Rol.RESPONSABLE_FARMACIA)  # A1 es el ejecutor


def test_aplicar_actualiza_existencia_solo_si_autorizado():
    a = ajuste()
    ex = Existencia("P1", "S1", 10, "L1")
    with pytest.raises(InvalidTransition):
        a.aplicar(ex)
    assert ex.cantidad == 10  # la existencia no cambia sin autorización
    a.autorizar("RF1", Rol.RESPONSABLE_FARMACIA)
    a.aplicar(ex)
    assert ex.cantidad == 7 and a.estado is EstadoAjuste.APLICADO
    assert a.events[-1].nombre == "AjusteDeInventarioAplicado"
    with pytest.raises(InvalidTransition):
        a.aplicar(ex)


def test_aplicar_valida_existencia_correcta_y_vigente():
    a = ajuste()
    a.autorizar("RF1", Rol.RESPONSABLE_FARMACIA)
    with pytest.raises(ReglaDeNegocioViolada):
        a.aplicar(Existencia("P9", "S1", 10, "L1"))
    with pytest.raises(ReglaDeNegocioViolada):
        a.aplicar(Existencia("P1", "S1", 12, "L1"))  # cambió desde la diferencia


def test_rechazar_y_estado_final():
    a = ajuste()
    a.rechazar("RF1", Rol.RESPONSABLE_FARMACIA)
    assert a.estado is EstadoAjuste.RECHAZADO
    with pytest.raises(InvalidTransition):
        a.autorizar("RF1", Rol.RESPONSABLE_FARMACIA)


def test_existencia_aplicar_ajuste_negativo():
    with pytest.raises(ReglaDeNegocioViolada):
        Existencia("P1", "S1", 1).aplicar_ajuste(-1)
