"""Casos de uso de inventario: retiros, diferencias, ajustes y consulta de existencias."""
from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.application.base import ServicioBase, nuevo_id
from src.domain.ajuste import AjusteDeInventario
from src.domain.diferencia import DiferenciaDeInventario
from src.domain.errors import NoEncontrado
from src.domain.retiro import RetiroDeLote
from src.domain.value_objects import Rol


@dataclass(frozen=True)
class ExistenciaConsultada:
    sucursal_id: str
    lote_id: Optional[str]
    cantidad: int
    clasificacion: Optional[str]
    retirado: bool


@dataclass(frozen=True)
class CaducidadConsultada:
    lote_id: str
    producto_id: str
    fecha_caducidad: date
    dias_restantes: int
    clasificacion: str
    retirado: bool

    @property
    def vendible(self) -> bool:
        return self.clasificacion != "CADUCADO" and not self.retirado


class InventarioApplicationService(ServicioBase):
    # --- Retiro de lote (US03, US04) ---
    def registrar_retiro(self, lote_id: str, motivo: str, usuario: str, rol: Rol,
                         retiro_id: Optional[str] = None) -> RetiroDeLote:
        with self._uow() as uow:
            lote = self._obtener(uow.lotes, lote_id, "Lote")
            retiro = RetiroDeLote.registrar(retiro_id or nuevo_id(), lote, motivo, usuario, rol)
            uow.lotes.guardar(lote)
            uow.retiros.guardar(retiro)
            self._auditar(uow, usuario, "REGISTRAR_RETIRO", "RetiroDeLote", retiro.id, "",
                          retiro.estado.value)
            uow.commit()
        self._publicar(retiro)
        return retiro

    def registrar_ejecucion_retiro(self, retiro_id: str, sucursal_id: str, identificadas: int,
                                   retiradas: int, usuario: str) -> RetiroDeLote:
        with self._uow() as uow:
            retiro = self._obtener(uow.retiros, retiro_id, "Retiro")
            antes = retiro.estado.value
            retiro.registrar_ejecucion(sucursal_id, identificadas, retiradas, usuario)
            uow.retiros.guardar(retiro)
            self._auditar(uow, usuario, "EJECUTAR_RETIRO", "RetiroDeLote", retiro.id, antes,
                          retiro.estado.value)
            uow.commit()
        return retiro

    def concluir_retiro(self, retiro_id: str, usuario: str) -> RetiroDeLote:
        with self._uow() as uow:
            retiro = self._obtener(uow.retiros, retiro_id, "Retiro")
            antes = retiro.estado.value
            retiro.concluir(usuario)
            uow.retiros.guardar(retiro)
            self._auditar(uow, usuario, "CONCLUIR_RETIRO", "RetiroDeLote", retiro.id, antes,
                          retiro.estado.value)
            uow.commit()
        self._publicar(retiro)
        return retiro

    # --- Diferencias (US15, US16) ---
    def registrar_diferencia(self, sucursal_id: str, producto_id: str, lote_id: Optional[str],
                             cantidad_fisica: int, usuario: str, prioritaria: bool = False,
                             diferencia_id: Optional[str] = None) -> DiferenciaDeInventario:
        with self._uow() as uow:
            ex = self._existencia(uow, producto_id, lote_id, sucursal_id)
            dif = DiferenciaDeInventario.registrar(
                diferencia_id or nuevo_id(), producto_id, sucursal_id, ex.cantidad,
                cantidad_fisica, usuario, lote_id, prioritaria, self._clock.ahora())
            uow.diferencias.guardar(dif)
            self._auditar(uow, usuario, "REGISTRAR_DIFERENCIA", "Diferencia", dif.id,
                          str(ex.cantidad), str(cantidad_fisica))
            uow.commit()
        self._publicar(dif)
        return dif

    def investigar_diferencia(self, diferencia_id: str, investigador_id: str, causa: str = "",
                              evidencia: str = "") -> DiferenciaDeInventario:
        with self._uow() as uow:
            dif = self._obtener(uow.diferencias, diferencia_id, "Diferencia")
            antes = dif.estado.value
            dif.registrar_investigacion(investigador_id, causa, evidencia)
            uow.diferencias.guardar(dif)
            self._auditar(uow, investigador_id, "INVESTIGAR_DIFERENCIA", "Diferencia", dif.id,
                          antes, dif.estado.value)
            uow.commit()
        self._publicar(dif)
        return dif

    # --- Ajustes (US17) ---
    def solicitar_ajuste(self, diferencia_id: str, ejecutor_id: str, motivo: str,
                         ajuste_id: Optional[str] = None) -> AjusteDeInventario:
        with self._uow() as uow:
            dif = self._obtener(uow.diferencias, diferencia_id, "Diferencia")
            ajuste = AjusteDeInventario.solicitar(ajuste_id or nuevo_id(), dif, ejecutor_id, motivo)
            uow.ajustes.guardar(ajuste)
            self._auditar(uow, ejecutor_id, "SOLICITAR_AJUSTE", "Ajuste", ajuste.id, "",
                          ajuste.estado.value)
            uow.commit()
        return ajuste

    def autorizar_ajuste(self, ajuste_id: str, usuario: str, rol: Rol) -> AjusteDeInventario:
        with self._uow() as uow:
            ajuste = self._obtener(uow.ajustes, ajuste_id, "Ajuste")
            antes = ajuste.estado.value
            ajuste.autorizar(usuario, rol)
            uow.ajustes.guardar(ajuste)
            self._auditar(uow, usuario, "AUTORIZAR_AJUSTE", "Ajuste", ajuste.id, antes,
                          ajuste.estado.value)
            uow.commit()
        self._publicar(ajuste)
        return ajuste

    def rechazar_ajuste(self, ajuste_id: str, usuario: str, rol: Rol) -> AjusteDeInventario:
        with self._uow() as uow:
            ajuste = self._obtener(uow.ajustes, ajuste_id, "Ajuste")
            antes = ajuste.estado.value
            ajuste.rechazar(usuario, rol)
            uow.ajustes.guardar(ajuste)
            self._auditar(uow, usuario, "RECHAZAR_AJUSTE", "Ajuste", ajuste.id, antes,
                          ajuste.estado.value)
            uow.commit()
        return ajuste

    def aplicar_ajuste(self, ajuste_id: str, usuario: str) -> AjusteDeInventario:
        with self._uow() as uow:
            ajuste = self._obtener(uow.ajustes, ajuste_id, "Ajuste")
            producto_id, lote_id, sucursal_id = ajuste.clave_existencia
            ex = self._existencia(uow, producto_id, lote_id, sucursal_id)
            antes = str(ex.cantidad)
            ajuste.aplicar(ex)
            uow.existencias.guardar(ex)
            uow.ajustes.guardar(ajuste)
            self._auditar(uow, usuario, "APLICAR_AJUSTE", "Ajuste", ajuste.id, antes,
                          str(ex.cantidad))
            uow.commit()
        self._publicar(ajuste)
        return ajuste

    # --- Consulta entre sucursales (US05, RN-03: informativa, sin reserva) ---
    def consultar_existencias(self, producto_id: str) -> list[ExistenciaConsultada]:
        with self._uow() as uow:
            self._obtener(uow.productos, producto_id, "Producto")
            resultado = []
            for ex in uow.existencias.listar_por_producto(producto_id):
                lote = uow.lotes.obtener(ex.lote_id) if ex.lote_id else None
                clasif = lote.clasificacion(self._clock.hoy()).value if lote else None
                resultado.append(ExistenciaConsultada(
                    ex.sucursal_id, ex.lote_id, ex.cantidad, clasif,
                    bool(lote and lote.retirado)))
            return resultado

    @staticmethod
    def _existencia(uow, producto_id, lote_id, sucursal_id):
        ex = uow.existencias.obtener(producto_id, lote_id, sucursal_id)
        if ex is None:
            raise NoEncontrado(f"No hay existencia de {producto_id}/{lote_id} en {sucursal_id}")
        return ex

    # --- Consultas (GET) ---
    def consultar_caducidad(self, lote_id: str) -> CaducidadConsultada:
        """US01 / RN-01: clasificación de un lote según los días restantes."""
        with self._uow() as uow:
            lote = self._obtener(uow.lotes, lote_id, "Lote")
            hoy = self._clock.hoy()
            return CaducidadConsultada(
                lote.id, lote.producto_id, lote.fecha_caducidad,
                (lote.fecha_caducidad - hoy).days, lote.clasificacion(hoy).value, lote.retirado)

    def obtener_retiro(self, retiro_id: str) -> RetiroDeLote:
        with self._uow() as uow:
            return self._obtener(uow.retiros, retiro_id, "Retiro")

    def obtener_diferencia(self, diferencia_id: str) -> DiferenciaDeInventario:
        with self._uow() as uow:
            return self._obtener(uow.diferencias, diferencia_id, "Diferencia")

    def obtener_ajuste(self, ajuste_id: str) -> AjusteDeInventario:
        with self._uow() as uow:
            return self._obtener(uow.ajustes, ajuste_id, "Ajuste")
