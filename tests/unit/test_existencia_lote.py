from datetime import date

import pytest

from src.domain.errors import ReglaDeNegocioViolada
from src.domain.existencia import Existencia
from src.domain.lote import Lote
from src.domain.value_objects import ClasificacionDeCaducidad as C


def test_descontar_ok_y_limite():
    e = Existencia("P1", "S1", 5, "L1")
    e.descontar(5)
    assert e.cantidad == 0


def test_descontar_insuficiente_o_invalido():
    e = Existencia("P1", "S1", 2)
    with pytest.raises(ReglaDeNegocioViolada):
        e.descontar(3)
    with pytest.raises(ReglaDeNegocioViolada):
        e.descontar(0)


def test_existencia_negativa_rechazada():
    with pytest.raises(ReglaDeNegocioViolada):
        Existencia("P1", "S1", -1)


def test_clave():
    assert Existencia("P1", "S1", 1, "L1").clave == ("P1", "L1", "S1")


def test_lote_clasificacion_y_retiro():
    lote = Lote("L1", "P1", date(2026, 11, 5))
    assert lote.clasificacion(date(2026, 11, 5)) is C.CADUCADO
    assert lote.esta_caducado(date(2026, 11, 5))
    lote.marcar_retirado()
    assert lote.retirado
