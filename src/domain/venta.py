"""Aggregate Venta con State Machine explícita (US02, US09, US13, US14; RN-05, RN-07)."""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from src.domain.errors import InvalidTransition, ReglaDeNegocioViolada
from src.domain.events import DomainEvent
from src.domain.value_objects import Dinero, EstadoVenta, ResultadoRevision

TRANSICIONES: dict[EstadoVenta, set[EstadoVenta]] = {
    EstadoVenta.EN_PROCESO: {EstadoVenta.COMPLETADA, EstadoVenta.CANCELADA},
    EstadoVenta.COMPLETADA: set(),
    EstadoVenta.CANCELADA: set(),
}
CAMPOS_DESCRIPTIVOS = {"observaciones"}  # RN-07: únicos corregibles tras completar


@dataclass(frozen=True)
class LineaDeVenta:
    producto_id: str
    cantidad: int
    precio_unitario: Dinero
    lote_id: Optional[str] = None
    requiere_receta: bool = False

    def __post_init__(self):
        if self.cantidad <= 0:
            raise ReglaDeNegocioViolada("Cantidad de línea debe ser > 0")

    @property
    def subtotal(self) -> Dinero:
        return self.precio_unitario.por(self.cantidad)


@dataclass
class Receta:
    folio: str
    medico: str
    cedula_medico: str
    nombre_paciente: str
    fecha_emision: date
    resultado: Optional[ResultadoRevision] = None
    revisada_por: Optional[str] = None


@dataclass
class Venta:
    id: str
    sucursal_id: str
    cajero_id: str
    estado: EstadoVenta = EstadoVenta.EN_PROCESO
    lineas: list[LineaDeVenta] = field(default_factory=list)
    receta: Optional[Receta] = None
    observaciones: str = ""
    correcciones: list[dict] = field(default_factory=list)
    events: list[DomainEvent] = field(default_factory=list)

    # --- consultas ---
    @property
    def total(self) -> Dinero:
        t = Dinero(Decimal("0"))
        for linea in self.lineas:
            t = t.sumar(linea.subtotal)
        return t

    @property
    def requiere_receta(self) -> bool:
        return any(linea.requiere_receta for linea in self.lineas)

    # --- state machine ---
    def _transicionar(self, destino: EstadoVenta) -> None:
        if destino not in TRANSICIONES[self.estado]:
            raise InvalidTransition(f"{self.estado.value} -> {destino.value} no permitida")
        self.estado = destino

    def _exigir_en_proceso(self) -> None:
        if self.estado is not EstadoVenta.EN_PROCESO:
            raise InvalidTransition("Solo una venta EN_PROCESO admite cambios (RN-07)")

    # --- comportamiento ---
    def agregar_linea(self, linea: LineaDeVenta) -> None:
        self._exigir_en_proceso()
        self.lineas.append(linea)

    def quitar_linea(self, indice: int) -> None:
        self._exigir_en_proceso()
        del self.lineas[indice]

    def sustituir_linea(self, producto_solicitado: str, nueva: LineaDeVenta) -> None:
        """US10: reemplaza la línea del producto solicitado por la alternativa autorizada."""
        self._exigir_en_proceso()
        for i, linea in enumerate(self.lineas):
            if linea.producto_id == producto_solicitado:
                self.lineas[i] = nueva
                return
        raise ReglaDeNegocioViolada(
            f"La venta no contiene el producto solicitado '{producto_solicitado}'")

    def registrar_revision_receta(
        self, receta: Receta, resultado: ResultadoRevision, responsable_id: str
    ) -> None:
        self._exigir_en_proceso()
        if not self.requiere_receta:
            raise ReglaDeNegocioViolada("La venta no contiene medicamentos con receta")
        receta.resultado, receta.revisada_por = resultado, responsable_id
        self.receta = receta
        self.events.append(
            DomainEvent("RecetaRevisada", self.id, {"resultado": resultado.value})
        )

    def completar(self) -> None:
        """Las reglas de validación las aplica ServicioDeValidacionDeVenta (DS-01)."""
        if not self.lineas:
            raise ReglaDeNegocioViolada("No se puede completar una venta sin productos")
        self._transicionar(EstadoVenta.COMPLETADA)
        self.events.append(DomainEvent("VentaCompletada", self.id))

    def cancelar(self, motivo: str = "") -> None:
        self._transicionar(EstadoVenta.CANCELADA)
        self.events.append(DomainEvent("VentaCancelada", self.id, {"motivo": motivo}))

    def corregir_dato_descriptivo(
        self, campo: str, nuevo_valor: str, motivo: str, ejecutor_id: str, autorizador_id: str
    ) -> None:
        """US14 / RN-07: sólo ventas completadas y sólo campos descriptivos."""
        if self.estado is not EstadoVenta.COMPLETADA:
            raise InvalidTransition("Sólo se corrigen ventas COMPLETADAS")
        if campo not in CAMPOS_DESCRIPTIVOS:
            raise ReglaDeNegocioViolada(f"'{campo}' no es un dato descriptivo corregible")
        if not motivo.strip():
            raise ReglaDeNegocioViolada("La corrección requiere motivo")
        self.correcciones.append({
            "campo": campo, "anterior": getattr(self, campo), "nuevo": nuevo_valor,
            "motivo": motivo, "ejecutor": ejecutor_id, "autorizador": autorizador_id,
            "fecha": datetime.now(timezone.utc).isoformat(),
        })
        setattr(self, campo, nuevo_valor)
