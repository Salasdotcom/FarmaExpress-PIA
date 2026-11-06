from dataclasses import dataclass
from typing import Optional

from src.domain.errors import ReglaDeNegocioViolada


@dataclass
class Existencia:
    """Aggregate root: cantidad registrada por producto, lote y sucursal."""
    producto_id: str
    sucursal_id: str
    cantidad: int
    lote_id: Optional[str] = None

    def __post_init__(self):
        if self.cantidad < 0:
            raise ReglaDeNegocioViolada("La existencia no puede ser negativa")

    @property
    def clave(self) -> tuple:
        return (self.producto_id, self.lote_id, self.sucursal_id)

    def hay_disponible(self, solicitada: int) -> bool:
        return solicitada <= self.cantidad

    def descontar(self, solicitada: int) -> None:
        if solicitada <= 0:
            raise ReglaDeNegocioViolada("Cantidad a descontar debe ser > 0")
        if not self.hay_disponible(solicitada):
            raise ReglaDeNegocioViolada("Existencia insuficiente")
        self.cantidad -= solicitada

    def aplicar_ajuste(self, cantidad_nueva: int) -> None:
        """Sólo lo invoca AjusteDeInventario autorizado (US17)."""
        if cantidad_nueva < 0:
            raise ReglaDeNegocioViolada("La existencia no puede ser negativa")
        self.cantidad = cantidad_nueva
