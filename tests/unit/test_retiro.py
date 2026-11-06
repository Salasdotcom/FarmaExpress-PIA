from datetime import date

import pytest

from src.domain.errors import InvalidTransition, PermisoDenegado, ReglaDeNegocioViolada
from src.domain.lote import Lote
from src.domain.retiro import EstadoRetiro, RetiroDeLote
from src.domain.value_objects import Rol


def nuevo():
    lote = Lote("L1", "P1", date(2027, 1, 1))
    return lote, RetiroDeLote.registrar("R1", lote, "alerta sanitaria", "RF1",
                                        Rol.RESPONSABLE_FARMACIA)


def test_registrar_bloquea_lote_y_emite_evento():
    lote, r = nuevo()
    assert lote.retirado and r.estado is EstadoRetiro.REGISTRADO
    assert r.events[0].nombre == "LoteRetirado"


def test_solo_responsable_registra():
    with pytest.raises(PermisoDenegado):
        RetiroDeLote.registrar("R", Lote("L", "P", date(2027, 1, 1)), "m", "A1", Rol.ALMACEN)


def test_registrar_requiere_motivo_y_lote_no_retirado():
    lote = Lote("L", "P", date(2027, 1, 1))
    with pytest.raises(ReglaDeNegocioViolada):
        RetiroDeLote.registrar("R", lote, " ", "RF1", Rol.RESPONSABLE_FARMACIA)
    lote.retirado = True
    with pytest.raises(ReglaDeNegocioViolada):
        RetiroDeLote.registrar("R", lote, "m", "RF1", Rol.RESPONSABLE_FARMACIA)


def test_ejecucion_y_conclusion():
    _, r = nuevo()
    r.registrar_ejecucion("S1", 10, 8, "A1")
    r.registrar_ejecucion("S2", 5, 5, "A1")
    assert r.estado is EstadoRetiro.EN_EJECUCION
    assert (r.total_identificadas, r.total_retiradas) == (15, 13)
    r.concluir("A1")
    assert r.estado is EstadoRetiro.EJECUTADO
    assert r.events[-1].nombre == "RetiroDeLoteEjecutado"


def test_ejecucion_cantidades_invalidas():
    _, r = nuevo()
    with pytest.raises(ReglaDeNegocioViolada):
        r.registrar_ejecucion("S1", 5, 6, "A1")  # límite: retiradas > identificadas
    with pytest.raises(ReglaDeNegocioViolada):
        r.registrar_ejecucion("S1", -1, 0, "A1")
    assert r.estado is EstadoRetiro.REGISTRADO


def test_concluir_sin_ejecucion_es_transicion_invalida():
    _, r = nuevo()
    with pytest.raises(InvalidTransition):
        r.concluir("A1")


def test_en_transito_bloquea_conclusion_hasta_resolverse():
    _, r = nuevo()
    r.registrar_ejecucion("S1", 5, 5, "A1")
    r.registrar_unidades_en_transito(3)
    with pytest.raises(ReglaDeNegocioViolada):
        r.concluir("A1")
    r.resolver_unidades_en_transito(3)
    r.concluir("A1")
    assert r.en_transito_pendiente == 0


def test_en_transito_validaciones():
    _, r = nuevo()
    with pytest.raises(ReglaDeNegocioViolada):
        r.registrar_unidades_en_transito(0)
    with pytest.raises(ReglaDeNegocioViolada):
        r.resolver_unidades_en_transito(1)


def test_retiro_ejecutado_no_admite_cambios():
    _, r = nuevo()
    r.registrar_ejecucion("S1", 1, 1, "A1")
    r.concluir("A1")
    with pytest.raises(InvalidTransition):
        r.registrar_ejecucion("S1", 1, 1, "A1")
    with pytest.raises(InvalidTransition):
        r.registrar_unidades_en_transito(1)
