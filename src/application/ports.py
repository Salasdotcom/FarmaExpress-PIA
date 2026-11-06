"""Puertos (interfaces) de la capa de aplicación. La infraestructura los implementa (DIP)."""
from datetime import date, datetime
from typing import Any, Optional, Protocol


class Clock(Protocol):
    def hoy(self) -> date: ...
    def ahora(self) -> datetime: ...


class IRepositorio(Protocol):
    def obtener(self, id: str) -> Optional[Any]: ...
    def guardar(self, entidad: Any) -> None: ...


class IExistenciaRepository(Protocol):
    def obtener(self, producto_id: str, lote_id: Optional[str], sucursal_id: str): ...
    def listar_por_producto(self, producto_id: str) -> list: ...
    def guardar(self, existencia) -> None: ...


class IAuditoria(Protocol):
    def registrar(self, usuario: str, accion: str, entidad: str, entidad_id: str,
                  antes: str, despues: str) -> None: ...


class IEventBus(Protocol):
    def publicar(self, evento) -> None: ...


class IUnitOfWork(Protocol):
    productos: IRepositorio
    ventas: IRepositorio
    lotes: IRepositorio
    existencias: IExistenciaRepository
    retiros: IRepositorio
    diferencias: IRepositorio
    ajustes: IRepositorio
    solicitudes: IRepositorio
    historial: IAuditoria

    def __enter__(self) -> "IUnitOfWork": ...
    def __exit__(self, et, ev, tb) -> Any: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
