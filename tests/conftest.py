"""Fixture `ctx`: cada prueba de aplicación corre contra memoria Y contra SQLAlchemy/SQLite,
para demostrar que ambos adaptadores cumplen el mismo contrato (los puertos)."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from src.application.inventario_service import InventarioApplicationService
from src.application.reposicion_service import ReposicionApplicationService
from src.application.venta_service import VentaApplicationService
from src.domain.existencia import Existencia
from src.domain.lote import Lote
from src.domain.producto import Producto
from src.domain.value_objects import CategoriaProducto, Dinero
from src.infrastructure import models as m
from src.infrastructure.db import crear_engine, crear_session_factory, init_db
from src.infrastructure.memory import InMemoryEventBus, InMemoryStore, InMemoryUnitOfWork
from src.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

HOY = date(2026, 11, 5)


class FakeClock:
    def hoy(self):
        return HOY

    def ahora(self):
        return datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


class _Coleccion:
    """Vista de sólo lectura tipo diccionario sobre un repositorio SQL (para aserciones)."""

    def __init__(self, engine, factory, repo, modelo):
        self._engine, self._factory, self._repo, self._modelo = engine, factory, repo, modelo

    def __getitem__(self, clave):
        with self._factory() as uow:
            repo = getattr(uow, self._repo)
            entidad = repo.obtener(*clave) if isinstance(clave, tuple) else repo.obtener(clave)
        if entidad is None:
            raise KeyError(clave)
        return entidad

    def __len__(self):
        with self._engine.connect() as con:
            return con.execute(select(func.count()).select_from(self._modelo)).scalar_one()


class VistaSql:
    def __init__(self, engine, factory):
        self._factory = factory
        for nombre, modelo in {
            "productos": m.ProductoRow, "ventas": m.VentaRow, "lotes": m.LoteRow,
            "existencias": m.ExistenciaRow, "retiros": m.RetiroRow,
            "diferencias": m.DiferenciaRow, "ajustes": m.AjusteRow,
            "solicitudes": m.SolicitudRow,
        }.items():
            setattr(self, nombre, _Coleccion(engine, factory, nombre, modelo))

    @property
    def historial(self):
        with self._factory() as uow:
            return uow.historial.listar()


class Ctx:
    def __init__(self, backend: str):
        self.engine = None
        if backend == "memory":
            self.store = InMemoryStore()
            factory = lambda: InMemoryUnitOfWork(self.store)  # noqa: E731
        else:
            engine = self.engine = crear_engine("sqlite+pysqlite:///:memory:")
            init_db(engine)
            sf = crear_session_factory(engine)
            factory = lambda: SqlAlchemyUnitOfWork(sf)  # noqa: E731
            self.store = VistaSql(engine, factory)
        self.factory = factory
        self.bus = InMemoryEventBus()
        clock = FakeClock()
        self.ventas = VentaApplicationService(factory, self.bus, clock)
        self.inventario = InventarioApplicationService(factory, self.bus, clock)
        self.reposicion = ReposicionApplicationService(factory, self.bus, clock)
        self._seed()

    def _seed(self):
        with self.factory() as uow:
            uow.productos.guardar(Producto("P1", "Paracetamol", Dinero(Decimal("50.00"))))
            uow.productos.guardar(Producto("P2", "Antibiótico", Dinero(Decimal("120.00")),
                                           CategoriaProducto.RECETA_SIMPLE))
            uow.productos.guardar(Producto("P3", "Descontinuado", Dinero(Decimal("10")),
                                           habilitado=False))
            uow.lotes.guardar(Lote("L1", "P1", date(2027, 6, 1)))
            uow.lotes.guardar(Lote("LC", "P1", HOY))  # caduca hoy
            uow.lotes.guardar(Lote("L2", "P2", date(2027, 6, 1)))
            for ex in (Existencia("P1", "S1", 10, "L1"), Existencia("P1", "S2", 4, "L1"),
                       Existencia("P1", "S1", 5, "LC"), Existencia("P2", "S1", 8, "L2")):
                uow.existencias.guardar(ex)
            uow.commit()
        self.seed_auditoria = len(self.store.historial)


@pytest.fixture(params=["memory", "sqlite"])
def ctx(request):
    c = Ctx(request.param)
    yield c
    if c.engine is not None:
        c.engine.dispose()  # cierra la conexión SQLite (evita ResourceWarning)
