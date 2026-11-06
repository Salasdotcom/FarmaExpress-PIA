import logging

logger = logging.getLogger("farmaexpress.eventos")


class LoggingEventBus:
    """Publica los Domain Events en el log (suficiente para el alcance del PIA)."""

    def publicar(self, evento) -> None:
        logger.info("evento=%s agregado=%s datos=%s", evento.nombre, evento.agregado_id,
                    evento.datos)
