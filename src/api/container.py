"""Raíz de composición: único lugar donde se conectan adaptadores y casos de uso."""
from dataclasses import dataclass
from typing import Any, Callable, Optional

from sqlalchemy import Engine

from src.application.auditoria_service import AuditoriaApplicationService
from src.application.inventario_service import InventarioApplicationService
from src.application.reposicion_service import ReposicionApplicationService
from src.application.venta_service import VentaApplicationService
from src.infrastructure.clock import SystemClock
from src.infrastructure.db import crear_engine, crear_session_factory
from src.infrastructure.event_bus import LoggingEventBus
from src.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@dataclass
class Container:
    engine: Engine
    uow_factory: Callable[[], Any]
    clock: Any
    ventas: VentaApplicationService
    inventario: InventarioApplicationService
    reposicion: ReposicionApplicationService
    auditoria: AuditoriaApplicationService


def build_container(database_url: Optional[str] = None, clock=None, bus=None) -> Container:
    engine = crear_engine(database_url)
    session_factory = crear_session_factory(engine)

    def uow_factory():
        return SqlAlchemyUnitOfWork(session_factory)

    clock = clock or SystemClock()
    bus = bus or LoggingEventBus()
    return Container(
        engine, uow_factory, clock,
        VentaApplicationService(uow_factory, bus, clock),
        InventarioApplicationService(uow_factory, bus, clock),
        ReposicionApplicationService(uow_factory, bus, clock),
        AuditoriaApplicationService(uow_factory, bus, clock),
    )
