"""Datos de demostración con fechas relativas a hoy, para que la demo siempre sea válida."""
from datetime import timedelta
from decimal import Decimal

from src.domain.existencia import Existencia
from src.domain.lote import Lote
from src.domain.producto import Producto
from src.domain.value_objects import CategoriaProducto as C
from src.domain.value_objects import Dinero


def cargar_demo(uow_factory, clock) -> bool:
    """Idempotente: devuelve False si ya había datos."""
    hoy = clock.hoy()
    with uow_factory() as uow:
        if uow.productos.obtener("MED-001") is not None:
            return False
        productos = [
            ("MED-001", "Paracetamol 500 mg", "35.50", C.VENTA_LIBRE, True),
            ("MED-002", "Ibuprofeno 400 mg", "52.00", C.VENTA_LIBRE, True),
            ("MED-003", "Amoxicilina 500 mg", "145.00", C.RECETA_SIMPLE, True),
            ("MED-004", "Clonazepam 2 mg", "210.00", C.CONTROLADO, True),
            ("MED-005", "Producto descontinuado", "10.00", C.VENTA_LIBRE, False),
        ]
        for id, desc, precio, cat, hab in productos:
            uow.productos.guardar(Producto(id, desc, Dinero(Decimal(precio)), cat, hab))
        lotes = [
            ("LOT-001", "MED-001", 400),   # NORMAL
            ("LOT-002", "MED-001", 45),    # PRÓXIMO A CADUCAR
            ("LOT-003", "MED-001", 7),     # CRÍTICO
            ("LOT-004", "MED-002", 0),     # CADUCA HOY -> CADUCADO (no vendible)
            ("LOT-005", "MED-003", 200),
            ("LOT-006", "MED-004", 300),
        ]
        for id, prod, dias in lotes:
            uow.lotes.guardar(Lote(id, prod, hoy + timedelta(days=dias)))
        existencias = [
            ("MED-001", "SUC-01", 50, "LOT-001"), ("MED-001", "SUC-02", 20, "LOT-001"),
            ("MED-001", "SUC-01", 30, "LOT-002"), ("MED-001", "SUC-01", 10, "LOT-003"),
            ("MED-002", "SUC-01", 12, "LOT-004"), ("MED-003", "SUC-01", 15, "LOT-005"),
            ("MED-003", "SUC-02", 5, "LOT-005"), ("MED-004", "SUC-01", 6, "LOT-006"),
        ]
        for prod, suc, cant, lote in existencias:
            uow.existencias.guardar(Existencia(prod, suc, cant, lote))
        uow.commit()
    return True
