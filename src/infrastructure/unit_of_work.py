from typing import Callable

from sqlalchemy.orm import Session

from src.infrastructure import repositories as r


class SqlAlchemyUnitOfWork:
    """Una transacción por caso de uso. Salir del bloque sin commit() hace rollback."""

    def __init__(self, session_factory: Callable[[], Session]):
        self._session_factory = session_factory
        self._session: Session | None = None
        self._committed = False

    def __enter__(self):
        s = self._session = self._session_factory()
        self._committed = False
        self.productos = r.SqlProductoRepo(s)
        self.ventas = r.SqlVentaRepo(s)
        self.lotes = r.SqlLoteRepo(s)
        self.existencias = r.SqlExistenciaRepo(s)
        self.retiros = r.SqlRetiroRepo(s)
        self.diferencias = r.SqlDiferenciaRepo(s)
        self.ajustes = r.SqlAjusteRepo(s)
        self.solicitudes = r.SqlSolicitudRepo(s)
        self.historial = r.SqlAuditoria(s)
        return self

    def __exit__(self, et, ev, tb):
        try:
            if not self._committed:
                self._session.rollback()
        finally:
            self._session.close()
        return False

    def commit(self) -> None:
        self._session.commit()
        self._committed = True

    def rollback(self) -> None:
        self._session.rollback()
