from decimal import Decimal

import pytest

from src.domain.errors import ReglaDeNegocioViolada
from src.domain.value_objects import Cantidad, Dinero


def test_cantidad_valida():
    assert Cantidad(0).valor == 0


@pytest.mark.parametrize("v", [-1, 1.5, True])
def test_cantidad_invalida(v):
    with pytest.raises(ReglaDeNegocioViolada):
        Cantidad(v)


def test_dinero_suma_y_por():
    assert Dinero(Decimal("10.50")).por(2).sumar(Dinero(Decimal("1"))).monto == Decimal("22.00")


def test_dinero_negativo_o_float_rechazado():
    with pytest.raises(ReglaDeNegocioViolada):
        Dinero(Decimal("-1"))
    with pytest.raises(ReglaDeNegocioViolada):
        Dinero(10.5)


def test_dinero_monedas_distintas():
    with pytest.raises(ReglaDeNegocioViolada):
        Dinero(Decimal("1")).sumar(Dinero(Decimal("1"), "USD"))
