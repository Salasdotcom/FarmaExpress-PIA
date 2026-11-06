"""Pruebas específicas de la persistencia SQL (archivo SQLite real, no sólo memoria)."""
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from src.application.inventario_service import InventarioApplicationService
from src.application.venta_service import ItemVenta, VentaApplicationService
from src.domain.existencia import Existencia
from src.domain.lote import Lote
from src.domain.producto import Producto
from src.domain.value_objects import Dinero, EstadoVenta, ResultadoRevision, Rol
from src.domain.venta import Receta
from src.infrastructure.db import (
    crear_engine,
    crear_session_factory,
    init_db,
    normalizar_url,
)
from src.infrastructure.memory import InMemoryEventBus
from src.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from tests.conftest import FakeClock


@pytest.fixture
def db(tmp_path):
    url = f"sqlite+pysqlite:///{tmp_path / 'farma.db'}"
    engine = crear_engine(url)
    init_db(engine)
    sf = crear_session_factory(engine)
    with SqlAlchemyUnitOfWork(sf) as uow:
        uow.productos.guardar(Producto("P1", "Paracetamol", Dinero(Decimal("49.99"))))
        uow.lotes.guardar(Lote("L1", "P1", date(2027, 6, 1)))
        uow.existencias.guardar(Existencia("P1", "S1", 10, "L1"))
        uow.existencias.guardar(Existencia("P1", "S1", 3))  # sin lote
        uow.commit()
    yield url, sf
    engine.dispose()


def servicios(sf):
    factory = lambda: SqlAlchemyUnitOfWork(sf)  # noqa: E731
    bus = InMemoryEventBus()
    return (VentaApplicationService(factory, bus, FakeClock()),
            InventarioApplicationService(factory, bus, FakeClock()), bus, factory)


def test_los_datos_sobreviven_a_un_reinicio(db):
    url, sf = db
    ventas, *_ = servicios(sf)
    ventas.crear_venta("S1", "C1", [ItemVenta("P1", 2, "L1")], "V1")
    ventas.completar_venta("V1", "C1")
    # "reinicio": nuevo engine y nuevas sesiones sobre el mismo archivo
    engine2 = crear_engine(url)
    try:
        ventas2, _, _, factory2 = servicios(crear_session_factory(engine2))
        v = ventas2.obtener_venta("V1")
        assert v.estado is EstadoVenta.COMPLETADA and len(v.lineas) == 1
        with factory2() as uow:
            assert uow.existencias.obtener("P1", "L1", "S1").cantidad == 8
            acciones = [h.accion for h in uow.historial.listar()]
            assert acciones == ["CREAR_VENTA", "COMPLETAR_VENTA"]
    finally:
        engine2.dispose()


def test_decimal_exacto_sin_flotantes(db):
    _, sf = db
    ventas, *_ = servicios(sf)
    ventas.crear_venta("S1", "C1", [ItemVenta("P1", 3, "L1")], "V1")
    total = ventas.obtener_venta("V1").total.monto
    assert total == Decimal("149.97") and isinstance(total, Decimal)


def test_existencia_sin_lote_y_con_lote_son_filas_distintas(db):
    _, sf = db
    with SqlAlchemyUnitOfWork(sf) as uow:
        assert uow.existencias.obtener("P1", None, "S1").cantidad == 3
        assert uow.existencias.obtener("P1", "L1", "S1").cantidad == 10
        assert len(uow.existencias.listar_por_producto("P1")) == 2


def test_rollback_no_deja_filas_a_medias(db):
    _, sf = db
    ventas, *_ = servicios(sf)
    with pytest.raises(Exception):  # noqa: B017  (producto inexistente en la 2a línea)
        ventas.crear_venta("S1", "C1", [ItemVenta("P1", 1, "L1"), ItemVenta("PX", 1)], "V9")
    with SqlAlchemyUnitOfWork(sf) as uow:
        assert uow.ventas.obtener("V9") is None
        assert uow.historial.listar() == []


def test_colecciones_hijas_se_actualizan_y_conservan_orden(db):
    _, sf = db
    ventas, *_ = servicios(sf)
    ventas.crear_venta("S1", "C1", [ItemVenta("P1", 1, "L1")], "V1")
    ventas.agregar_linea("V1", ItemVenta("P1", 2, "L1"), "C1")
    ventas.agregar_linea("V1", ItemVenta("P1", 3, "L1"), "C1")
    assert [li.cantidad for li in ventas.obtener_venta("V1").lineas] == [1, 2, 3]
    with SqlAlchemyUnitOfWork(sf) as uow:  # quitar una línea elimina su fila (delete-orphan)
        v = uow.ventas.obtener("V1")
        v.quitar_linea(1)
        uow.ventas.guardar(v)
        uow.commit()
    assert [li.cantidad for li in ventas.obtener_venta("V1").lineas] == [1, 3]


def test_receta_y_correcciones_hacen_ida_y_vuelta(db):
    _, sf = db
    ventas, *_ = servicios(sf)
    ventas.crear_venta("S1", "C1", [ItemVenta("P1", 1, "L1")], "V1")
    with SqlAlchemyUnitOfWork(sf) as uow:  # marca la línea como de receta para el flujo
        v = uow.ventas.obtener("V1")
        object.__setattr__(v.lineas[0], "requiere_receta", True)
        uow.ventas.guardar(v)
        uow.commit()
    rec = Receta("R1", "Dr. X", "123", "Paciente", date(2026, 11, 1))
    ventas.revisar_receta("V1", rec, ResultadoRevision.ACEPTADA, "RF1", Rol.RESPONSABLE_FARMACIA)
    ventas.completar_venta("V1", "C1")
    with SqlAlchemyUnitOfWork(sf) as uow:
        v = uow.ventas.obtener("V1")
        v.corregir_dato_descriptivo("observaciones", "ok", "typo", "C1", "RF1")
        uow.ventas.guardar(v)
        uow.commit()
    v = ventas.obtener_venta("V1")
    assert v.receta.resultado is ResultadoRevision.ACEPTADA and v.receta.folio == "R1"
    assert v.receta.fecha_emision == date(2026, 11, 1)
    assert v.observaciones == "ok" and v.correcciones[0]["motivo"] == "typo"


def test_fechas_vuelven_con_zona_horaria_utc(db):
    _, sf = db
    _, inv, _, _ = servicios(sf)
    d = inv.registrar_diferencia("S1", "P1", "L1", 7, "A1", diferencia_id="D1")
    with SqlAlchemyUnitOfWork(sf) as uow:
        leida = uow.diferencias.obtener("D1")
        assert leida.fecha_conteo == d.fecha_conteo == datetime(2026, 11, 5, 12, 0,
                                                                tzinfo=timezone.utc)
        assert uow.historial.listar()[0].fecha.tzinfo is not None


def test_retiro_con_ejecuciones_persiste_en_orden(db):
    _, sf = db
    _, inv, _, _ = servicios(sf)
    inv.registrar_retiro("L1", "alerta", "RF1", Rol.RESPONSABLE_FARMACIA, "R1")
    inv.registrar_ejecucion_retiro("R1", "S1", 10, 8, "A1")
    inv.registrar_ejecucion_retiro("R1", "S2", 5, 5, "A1")
    with SqlAlchemyUnitOfWork(sf) as uow:
        r = uow.retiros.obtener("R1")
        assert [e.sucursal_id for e in r.ejecuciones] == ["S1", "S2"]
        assert uow.lotes.obtener("L1").retirado


def test_normalizar_url_y_engine_por_defecto(monkeypatch):
    esperado = "postgresql+psycopg2://u:p@h/db"
    assert normalizar_url("postgres://u:p@h/db") == esperado
    assert normalizar_url("postgresql://u:p@h/db") == esperado
    assert normalizar_url(esperado) == esperado           # ya trae driver: no se toca
    assert normalizar_url("sqlite+pysqlite:///:memory:") == "sqlite+pysqlite:///:memory:"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    e1 = crear_engine()
    assert e1.url.drivername == "sqlite+pysqlite"
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    e2 = crear_engine()
    assert e2.dialect.name == "sqlite"
    e1.dispose()
    e2.dispose()
