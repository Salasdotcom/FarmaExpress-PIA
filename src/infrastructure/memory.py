"""Adaptadores en memoria: repositorios, Unit of Work con rollback y bus de eventos."""
import copy
from datetime import datetime, timezone
from typing import Any, Optional

from src.domain.auditoria import RegistroAuditoria


class InMemoryStore:
    COLECCIONES = ("productos", "ventas", "lotes", "existencias", "retiros", "diferencias",
                   "ajustes", "solicitudes", "historial")

    def __init__(self):
        for nombre in self.COLECCIONES:
            setattr(self, nombre, [] if nombre == "historial" else {})

    def snapshot(self) -> dict:
        return copy.deepcopy(self.__dict__)

    def restore(self, snap: dict) -> None:
        self.__dict__.update(snap)


class _Repo:
    def __init__(self, store: InMemoryStore, nombre: str):
        self._store, self._nombre = store, nombre

    def _datos(self):
        return getattr(self._store, self._nombre)

    def obtener(self, id: str) -> Optional[Any]:
        return self._datos().get(id)

    def guardar(self, entidad: Any) -> None:
        self._datos()[entidad.id] = entidad


class _ExistenciaRepo(_Repo):
    def obtener(self, producto_id, lote_id, sucursal_id):
        return self._datos().get((producto_id, lote_id, sucursal_id))

    def listar_por_producto(self, producto_id):
        return [e for e in self._datos().values() if e.producto_id == producto_id]

    def guardar(self, existencia) -> None:
        self._datos()[existencia.clave] = existencia


class _Auditoria:
    def __init__(self, store: InMemoryStore):
        self._store = store

    def registrar(self, usuario, accion, entidad, entidad_id, antes, despues) -> None:
        self._store.historial.append(RegistroAuditoria(
            usuario, accion, entidad, entidad_id, antes, despues, datetime.now(timezone.utc)))

    def listar(self) -> list:
        return list(self._store.historial)


class InMemoryUnitOfWork:
    """Salir del bloque sin commit() (o con excepción) restaura el estado inicial."""

    def __init__(self, store: InMemoryStore):
        self._store = store
        self._snap = None
        self._committed = False

    def __enter__(self):
        self._snap = self._store.snapshot()
        self._committed = False
        s = self._store
        self.productos = _Repo(s, "productos")
        self.ventas = _Repo(s, "ventas")
        self.lotes = _Repo(s, "lotes")
        self.existencias = _ExistenciaRepo(s, "existencias")
        self.retiros = _Repo(s, "retiros")
        self.diferencias = _Repo(s, "diferencias")
        self.ajustes = _Repo(s, "ajustes")
        self.solicitudes = _Repo(s, "solicitudes")
        self.historial = _Auditoria(s)
        return self

    def __exit__(self, et, ev, tb):
        if not self._committed:
            self.rollback()
        return False

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        self._store.restore(self._snap)


class InMemoryEventBus:
    def __init__(self):
        self.publicados: list = []

    def publicar(self, evento) -> None:
        self.publicados.append(evento)
