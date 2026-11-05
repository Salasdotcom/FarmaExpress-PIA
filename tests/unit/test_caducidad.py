from datetime import date, timedelta

import pytest

from src.domain.value_objects import ClasificacionDeCaducidad as C
from src.domain.value_objects import clasificar_caducidad

HOY = date(2026, 11, 5)


@pytest.mark.parametrize("dias,esperado", [
    (365, C.NORMAL), (91, C.NORMAL),            # éxito / límite
    (90, C.PROXIMO), (11, C.PROXIMO),           # límites
    (10, C.CRITICO), (1, C.CRITICO),            # límites
    (0, C.CADUCADO), (-1, C.CADUCADO),          # hoy = caducidad -> caducado
])
def test_clasificacion_rn01(dias, esperado):
    assert clasificar_caducidad(HOY + timedelta(days=dias), HOY) is esperado
