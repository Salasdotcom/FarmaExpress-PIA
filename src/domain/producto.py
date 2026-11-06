from dataclasses import dataclass

from src.domain.value_objects import CategoriaProducto, Dinero


@dataclass
class Producto:
    id: str
    descripcion: str
    precio: Dinero
    categoria: CategoriaProducto = CategoriaProducto.VENTA_LIBRE
    habilitado: bool = True

    @property
    def requiere_receta(self) -> bool:
        return self.categoria is not CategoriaProducto.VENTA_LIBRE
