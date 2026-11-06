"""Carga de los CSV del paquete de pruebas y ejecución de casos/transiciones (Fase 4).

Mapeo documentado (ver docs/fixtures_mapeo.md):
  catalogo.csv -> Producto + Lote LOT-<id> + Existencia en SUC-01 (stock = capacidad_o_stock)
  operaciones.csv + detalle_operaciones.csv -> Venta (estado inicial CREADO == EN_PROCESO)
  actores.csv -> OperacionEvaluable (el actor comprador no forma parte del agregado Venta)
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional

from src.application.venta_service import ItemVenta, VentaApplicationService
from src.domain.elegibilidad import (
    OperacionEvaluable,
    evaluar_beneficio,
    evaluar_procesable,
)
from src.domain.errors import DomainError, ReglaDeNegocioViolada
from src.domain.existencia import Existencia
from src.domain.lote import Lote
from src.domain.producto import Producto
from src.domain.value_objects import Dinero
from src.infrastructure.memory import InMemoryEventBus, InMemoryStore, InMemoryUnitOfWork

SUCURSAL = "SUC-01"
CAJERO = "CAJ-FIXTURE"
HOY = date(2026, 11, 5)


class RelojFijo:
    def hoy(self):
        return HOY

    def ahora(self):
        return datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


def leer(carpeta: Path, nombre: str) -> list[dict]:
    with open(Path(carpeta) / nombre, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


@dataclass
class Paquete:
    actores: dict[str, dict]
    catalogo: dict[str, dict]
    operaciones: list[dict]
    detalle: dict[str, list[dict]]
    casos: list[dict]
    transiciones: list[dict]


def cargar_paquete(carpeta: Path) -> Paquete:
    detalle: dict[str, list[dict]] = {}
    for fila in leer(carpeta, "detalle_operaciones.csv"):
        detalle.setdefault(fila["operacion_id"], []).append(fila)
    return Paquete(
        actores={a["actor_id"]: a for a in leer(carpeta, "actores.csv")},
        catalogo={r["recurso_id"]: r for r in leer(carpeta, "catalogo.csv")},
        operaciones=leer(carpeta, "operaciones.csv"),
        detalle=detalle,
        casos=leer(carpeta, "casos_prueba.csv"),
        transiciones=leer(carpeta, "transiciones_prueba.csv"),
    )


def total_de(paquete: Paquete, operacion_id: str) -> Dinero:
    """total = suma(precio_mxn x cantidad) con Decimal."""
    total = Decimal("0")
    for linea in paquete.detalle.get(operacion_id, []):
        total += Decimal(paquete.catalogo[linea["recurso_id"]]["precio_mxn"]) * int(
            linea["cantidad"])
    return Dinero(total)


def evaluable(paquete: Paquete, operacion_id: str) -> OperacionEvaluable:
    op = next(o for o in paquete.operaciones if o["operacion_id"] == operacion_id)
    actor = paquete.actores[op["actor_id"]]
    return OperacionEvaluable(
        operacion_id=operacion_id, actor_id=actor["actor_id"],
        actor_activo=actor["activo"] == "1", actor_preferente=actor["es_preferente"] == "1",
        numero_de_lineas=len(paquete.detalle.get(operacion_id, [])),
        total=total_de(paquete, operacion_id),
        promocion_activa=op["promocion_activa"] == "1", autorizada=op["autorizado"] == "1")


# ------------------------------ casos de prueba ------------------------------
def ejecutar_caso(paquete: Paquete, caso: dict) -> dict:
    op = evaluable(paquete, caso["operacion_id"])
    if caso["tipo_prueba"] == "validar_operacion":
        d = evaluar_procesable(op)
        texto = "VALIDA" if d.cumple else "NO VALIDA: " + ", ".join(d.incumplidas)
    else:
        d = evaluar_beneficio(op)
        texto = "CON BENEFICIO" if d.cumple else "SIN BENEFICIO: " + ", ".join(d.incumplidas)
    return {**caso, "resultado_alumno": texto, "total_mxn": f"{op.total.monto:.2f}",
            "cumple": "1" if d.cumple else "0"}


# ------------------------------ transiciones ------------------------------
@dataclass
class Entorno:
    store: InMemoryStore
    bus: InMemoryEventBus
    ventas: VentaApplicationService


def crear_entorno(paquete: Paquete) -> Entorno:
    store = InMemoryStore()
    bus = InMemoryEventBus()
    ventas = VentaApplicationService(lambda: InMemoryUnitOfWork(store), bus, RelojFijo())
    for r in paquete.catalogo.values():
        pid = r["recurso_id"]
        store.productos[pid] = Producto(pid, r["descripcion"], Dinero(Decimal(r["precio_mxn"])),
                                        habilitado=r["habilitado"] == "1")
        store.lotes[f"LOT-{pid}"] = Lote(f"LOT-{pid}", pid, HOY + timedelta(days=365))
        ex = Existencia(pid, SUCURSAL, int(r["capacidad_o_stock"]), f"LOT-{pid}")
        store.existencias[ex.clave] = ex
    return Entorno(store, bus, ventas)


def _crear_venta(paquete: Paquete, entorno: Entorno, operacion_id: str):
    items = [ItemVenta(ln["recurso_id"], int(ln["cantidad"]), f"LOT-{ln['recurso_id']}")
             for ln in paquete.detalle.get(operacion_id, [])]
    return entorno.ventas.crear_venta(SUCURSAL, CAJERO, items, venta_id=f"V-{operacion_id}")


def ejecutar_transicion(paquete: Paquete, fila: dict, entorno: Optional[Entorno] = None) -> dict:
    """Ejecuta la acción contra el servicio real; devuelve estado final y evento/excepción."""
    entorno = entorno or crear_entorno(paquete)
    accion, op_id = fila["accion_sugerida"], fila["operacion_id"]
    estado: str = fila["estado_inicial"]
    resultado = ""
    try:
        venta = _crear_venta(paquete, entorno, op_id)
        estado = venta.estado.value
        if accion != "cancelar":
            d = evaluar_procesable(evaluable(paquete, op_id))
            if not d.cumple:     # precondición del modelo de pruebas (puede_procesarse)
                raise ReglaDeNegocioViolada("Operación no procesable: " + ", ".join(d.incumplidas))
        if accion in ("completar", "aprobar"):
            venta = entorno.ventas.completar_venta(venta.id, CAJERO)
        elif accion == "cancelar":
            venta = entorno.ventas.cancelar_venta(venta.id, CAJERO, "caso de prueba")
        elif accion == "repetir_aprobacion":
            entorno.ventas.completar_venta(venta.id, CAJERO)
            venta = entorno.ventas.completar_venta(venta.id, CAJERO)     # 2.ª vez -> 409
        elif accion == "saltar_estado":
            entorno.ventas.cancelar_venta(venta.id, CAJERO, "caso de prueba")
            venta = entorno.ventas.completar_venta(venta.id, CAJERO)     # desde terminal -> 409
        estado = venta.estado.value
        resultado = "OK"
    except DomainError as e:
        if f"V-{op_id}" in entorno.store.ventas:
            estado = entorno.ventas.obtener_venta(f"V-{op_id}").estado.value
        resultado = f"EXCEPCION {type(e).__name__}: {e}"
    eventos = [e.nombre for e in entorno.bus.publicados]
    return {**fila, "estado_final": estado, "evento": ", ".join(eventos),
            "resultado_alumno": resultado}
