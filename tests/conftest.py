from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from src.application.inventario_service import InventarioApplicationService
from src.application.reposicion_service import ReposicionApplicationService
from src.application.venta_service import VentaApplicationService
from src.domain.existencia import Existencia
from src.domain.lote import Lote
from src.domain.producto import Producto
from src.domain.value_objects import CategoriaProducto, Dinero
from src.infrastructure.memory import InMemoryEventBus, InMemoryStore, InMemoryUnitOfWork

HOY = date(2026, 11, 5)


class FakeClock:
    def hoy(self):
        return HOY

    def ahora(self):
        return datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


class Ctx:
    def __init__(self):
        self.store = InMemoryStore()
        self.bus = InMemoryEventBus()
        clock = FakeClock()

        def factory():
            return InMemoryUnitOfWork(self.store)

        self.ventas = VentaApplicationService(factory, self.bus, clock)
        self.inventario = InventarioApplicationService(factory, self.bus, clock)
        self.reposicion = ReposicionApplicationService(factory, self.bus, clock)
        self._seed()

    def _seed(self):
        s = self.store
        s.productos["P1"] = Producto("P1", "Paracetamol", Dinero(Decimal("50.00")))
        s.productos["P2"] = Producto("P2", "Antibiótico", Dinero(Decimal("120.00")),
                                     CategoriaProducto.RECETA_SIMPLE)
        s.productos["P3"] = Producto("P3", "Descontinuado", Dinero(Decimal("10")), habilitado=False)
        s.lotes["L1"] = Lote("L1", "P1", date(2027, 6, 1))
        s.lotes["LC"] = Lote("LC", "P1", HOY)                 # caduca hoy
        s.lotes["L2"] = Lote("L2", "P2", date(2027, 6, 1))
        for ex in (Existencia("P1", "S1", 10, "L1"), Existencia("P1", "S2", 4, "L1"),
                   Existencia("P1", "S1", 5, "LC"), Existencia("P2", "S1", 8, "L2")):
            s.existencias[ex.clave] = ex


@pytest.fixture
def ctx():
    return Ctx()
