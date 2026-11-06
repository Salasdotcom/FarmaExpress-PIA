"""Excepciones de dominio. La API las traduce a HTTP (409 / 422)."""


class DomainError(Exception):
    pass


class InvalidTransition(DomainError):
    """Transición de estado no permitida (-> HTTP 409)."""


class ReglaDeNegocioViolada(DomainError):
    """Dato o regla inválida (-> HTTP 422)."""


class PermisoDenegado(DomainError):
    """El rol o usuario no puede ejecutar la acción (-> HTTP 403)."""
