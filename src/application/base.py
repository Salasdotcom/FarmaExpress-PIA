from typing import Any, Callable
from uuid import uuid4

from src.application.ports import Clock, IEventBus, IUnitOfWork
from src.domain.errors import NoEncontrado


def nuevo_id(prefijo: str = "ID") -> str:
    """Folio corto y legible (p. ej. VTA-3F9A2C1B) en lugar de un UUID de 32 caracteres."""
    return f"{prefijo}-{uuid4().hex[:8].upper()}"


class ServicioBase:
    def __init__(self, uow_factory: Callable[[], IUnitOfWork], bus: IEventBus, clock: Clock):
        self._uow = uow_factory
        self._bus = bus
        self._clock = clock

    @staticmethod
    def _obtener(repo, id: str, nombre: str) -> Any:
        entidad = repo.obtener(id)
        if entidad is None:
            raise NoEncontrado(f"{nombre} '{id}' no existe")
        return entidad

    @staticmethod
    def _auditar(uow: IUnitOfWork, usuario: str, accion: str, entidad: str, id: str,
                 antes: str, despues: str) -> None:
        uow.historial.registrar(usuario, accion, entidad, id, antes, despues)

    def _publicar(self, *agregados) -> None:
        """Los eventos se publican sólo después de confirmar la transacción."""
        for agregado in agregados:
            for evento in list(agregado.events):
                self._bus.publicar(evento)
            agregado.events.clear()
