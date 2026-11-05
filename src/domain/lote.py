from dataclasses import dataclass
from datetime import date

from src.domain.value_objects import ClasificacionDeCaducidad, clasificar_caducidad


@dataclass
class Lote:
    id: str
    producto_id: str
    fecha_caducidad: date
    retirado: bool = False

    def clasificacion(self, hoy: date) -> ClasificacionDeCaducidad:
        return clasificar_caducidad(self.fecha_caducidad, hoy)

    def esta_caducado(self, hoy: date) -> bool:
        return self.clasificacion(hoy) is ClasificacionDeCaducidad.CADUCADO

    def marcar_retirado(self) -> None:
        self.retirado = True
