"""Casos de uso de Venta. completar_venta sigue el flujo DS-01 (y DS-02 si falla)."""
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Sequence

from src.application.base import ServicioBase, nuevo_id
from src.domain.errors import (
    InvalidTransition,
    ReglaDeNegocioViolada,
    ValidacionDeVentaFallida,
)
from src.domain.permisos import exigir_rol
from src.domain.services import ServicioDeValidacionDeVenta
from src.domain.specifications import ContextoDeValidacion
from src.domain.sustitucion import SustitucionDeVenta
from src.domain.value_objects import EstadoVenta, ResultadoRevision, Rol
from src.domain.venta import LineaDeVenta, Receta, Venta


@dataclass(frozen=True)
class ItemVenta:
    producto_id: str
    cantidad: int
    lote_id: Optional[str] = None


class VentaApplicationService(ServicioBase):
    def __init__(self, uow_factory, bus, clock,
                 validador: Optional[ServicioDeValidacionDeVenta] = None):
        super().__init__(uow_factory, bus, clock)
        self._validador = validador or ServicioDeValidacionDeVenta()

    def _linea(self, uow, item: ItemVenta) -> LineaDeVenta:
        producto = self._obtener(uow.productos, item.producto_id, "Producto")
        if not producto.habilitado:
            raise ReglaDeNegocioViolada(f"El producto {producto.id} no está habilitado")
        if item.lote_id is not None:
            self._obtener(uow.lotes, item.lote_id, "Lote")
        return LineaDeVenta(producto.id, item.cantidad, producto.precio, item.lote_id,
                            producto.requiere_receta)

    def crear_venta(self, sucursal_id: str, cajero_id: str, items: Sequence[ItemVenta],
                    venta_id: Optional[str] = None) -> Venta:
        with self._uow() as uow:
            venta = Venta(venta_id or nuevo_id(), sucursal_id, cajero_id)
            for item in items:
                venta.agregar_linea(self._linea(uow, item))
            uow.ventas.guardar(venta)
            self._auditar(uow, cajero_id, "CREAR_VENTA", "Venta", venta.id, "",
                          venta.estado.value)
            uow.commit()
        return venta

    def agregar_linea(self, venta_id: str, item: ItemVenta, usuario: str) -> Venta:
        with self._uow() as uow:
            venta = self._obtener(uow.ventas, venta_id, "Venta")
            venta.agregar_linea(self._linea(uow, item))
            uow.ventas.guardar(venta)
            self._auditar(uow, usuario, "AGREGAR_LINEA", "Venta", venta.id, "", item.producto_id)
            uow.commit()
        return venta

    def obtener_venta(self, venta_id: str) -> Venta:
        with self._uow() as uow:
            return self._obtener(uow.ventas, venta_id, "Venta")

    def cancelar_venta(self, venta_id: str, usuario: str, motivo: str = "") -> Venta:
        with self._uow() as uow:
            venta = self._obtener(uow.ventas, venta_id, "Venta")
            antes = venta.estado.value
            venta.cancelar(motivo)
            uow.ventas.guardar(venta)
            self._auditar(uow, usuario, "CANCELAR_VENTA", "Venta", venta.id, antes,
                          venta.estado.value)
            uow.commit()
        self._publicar(venta)
        return venta

    def revisar_receta(self, venta_id: str, receta: Receta, resultado: ResultadoRevision,
                       responsable_id: str, rol: Rol) -> Venta:
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        with self._uow() as uow:
            venta = self._obtener(uow.ventas, venta_id, "Venta")
            venta.registrar_revision_receta(receta, resultado, responsable_id)
            uow.ventas.guardar(venta)
            self._auditar(uow, responsable_id, "REVISAR_RECETA", "Venta", venta.id, "",
                          resultado.value)
            uow.commit()
        self._publicar(venta)
        return venta

    def completar_venta(self, venta_id: str, usuario: str) -> Venta:
        """DS-01: begin -> obtener -> validar -> descontar -> completar -> guardar -> commit.
        Si la validación falla (DS-02) o algo lanza, no queda ningún cambio (rollback)."""
        with self._uow() as uow:
            venta = self._obtener(uow.ventas, venta_id, "Venta")
            if venta.estado is not EstadoVenta.EN_PROCESO:
                raise InvalidTransition(
                    f"La venta está {venta.estado.value}; no puede completarse")
            lotes, existencias = {}, {}
            for linea in venta.lineas:
                if linea.lote_id and linea.lote_id not in lotes:
                    lote = uow.lotes.obtener(linea.lote_id)
                    if lote is not None:
                        lotes[linea.lote_id] = lote
                ex = uow.existencias.obtener(linea.producto_id, linea.lote_id, venta.sucursal_id)
                if ex is not None:
                    existencias[ex.clave] = ex
            ctx = ContextoDeValidacion(venta, self._clock.hoy(), lotes, existencias)
            resultado = self._validador.validar(ctx)
            if not resultado.valida:
                raise ValidacionDeVentaFallida(resultado.violaciones)
            pedido = defaultdict(int)
            for linea in venta.lineas:
                pedido[(linea.producto_id, linea.lote_id, venta.sucursal_id)] += linea.cantidad
            for clave, cantidad in pedido.items():
                existencias[clave].descontar(cantidad)
                uow.existencias.guardar(existencias[clave])
            venta.completar()
            uow.ventas.guardar(venta)
            self._auditar(uow, usuario, "COMPLETAR_VENTA", "Venta", venta.id,
                          EstadoVenta.EN_PROCESO.value, venta.estado.value)
            uow.commit()
        self._publicar(venta)
        return venta

    # --- US10: sustituciones (sólo responsable de farmacia) ---
    def autorizar_sustitucion(self, venta_id: str, producto_solicitado: str, alternativa_id: str,
                              motivo: str, responsable_id: str, rol: Rol,
                              lote_id: Optional[str] = None) -> SustitucionDeVenta:
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        with self._uow() as uow:
            venta = self._obtener(uow.ventas, venta_id, "Venta")
            sust = SustitucionDeVenta.autorizar(
                nuevo_id(), venta.id, producto_solicitado, alternativa_id, motivo,
                responsable_id, rol, self._clock.ahora())
            original = next((li for li in venta.lineas if li.producto_id == producto_solicitado),
                            None)
            if original is None:
                raise ReglaDeNegocioViolada(
                    f"La venta no contiene el producto solicitado '{producto_solicitado}'")
            nueva = self._linea(uow, ItemVenta(alternativa_id, original.cantidad, lote_id))
            venta.sustituir_linea(producto_solicitado, nueva)
            uow.ventas.guardar(venta)
            uow.sustituciones.guardar(sust)
            self._auditar(uow, responsable_id, "AUTORIZAR_SUSTITUCION", "Venta", venta.id,
                          producto_solicitado, alternativa_id)
            uow.commit()
        self._publicar(sust)
        return sust

    def rechazar_sustitucion(self, venta_id: str, producto_solicitado: str, motivo: str,
                             responsable_id: str, rol: Rol) -> SustitucionDeVenta:
        """Sin alternativa aceptada: se registra la decisión y la venta no cambia."""
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        with self._uow() as uow:
            venta = self._obtener(uow.ventas, venta_id, "Venta")
            sust = SustitucionDeVenta.rechazar(
                nuevo_id(), venta.id, producto_solicitado, motivo, responsable_id, rol,
                self._clock.ahora())
            uow.sustituciones.guardar(sust)
            self._auditar(uow, responsable_id, "RECHAZAR_SUSTITUCION", "Venta", venta.id,
                          producto_solicitado, "")
            uow.commit()
        self._publicar(sust)
        return sust

    # --- US14: corrección de datos descriptivos (sólo responsable de farmacia) ---
    def corregir_venta_completada(self, venta_id: str, campo: str, nuevo_valor: str, motivo: str,
                                  autorizador_id: str, rol: Rol,
                                  solicitante_id: Optional[str] = None) -> Venta:
        exigir_rol(rol, Rol.RESPONSABLE_FARMACIA)
        with self._uow() as uow:
            venta = self._obtener(uow.ventas, venta_id, "Venta")
            anterior = getattr(venta, campo, "") if campo == "observaciones" else ""
            venta.corregir_dato_descriptivo(
                campo, nuevo_valor, motivo, solicitante_id or autorizador_id, autorizador_id)
            uow.ventas.guardar(venta)
            self._auditar(uow, autorizador_id, "CORREGIR_VENTA", "Venta", venta.id,
                          str(anterior), nuevo_valor)
            uow.commit()
        self._publicar(venta)
        return venta
