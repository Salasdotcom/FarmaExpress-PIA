"""Excepciones de dominio. La API las traduce a HTTP (409 / 422)."""


class DomainError(Exception):
    pass


class InvalidTransition(DomainError):
    """Transición de estado no permitida (-> HTTP 409)."""


class ReglaDeNegocioViolada(DomainError):
    """Dato o regla inválida (-> HTTP 422)."""


class PermisoDenegado(DomainError):
    """El rol o usuario no puede ejecutar la acción (-> HTTP 403)."""


class NoEncontrado(DomainError):
    """Recurso inexistente (-> HTTP 404)."""


class ValidacionDeVentaFallida(ReglaDeNegocioViolada):
    """La venta incumple una o más reglas (-> HTTP 422); lista los códigos."""

    def __init__(self, violaciones):
        self.violaciones = tuple(violaciones)
        super().__init__("Venta no completable: " + ", ".join(self.violaciones))
