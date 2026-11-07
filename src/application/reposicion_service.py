"""Casos de uso de reposición (US06, US07, US08)."""
from typing import Optional

from src.application.base import ServicioBase, nuevo_id
from src.domain.solicitud_compra import MotivoNecesidad, NecesidadReposicion, SolicitudDeCompra
from src.domain.value_objects import Rol


class ReposicionApplicationService(ServicioBase):
    def crear_solicitud(self, sucursal_id: str, usuario: str,
                        solicitud_id: Optional[str] = None) -> SolicitudDeCompra:
        with self._uow() as uow:
            s = SolicitudDeCompra(solicitud_id or nuevo_id("SOL"), sucursal_id)
            uow.solicitudes.guardar(s)
            self._auditar(uow, usuario, "CREAR_SOLICITUD", "SolicitudDeCompra", s.id, "",
                          s.estado.value)
            uow.commit()
        return s

    def registrar_necesidad(self, solicitud_id: str, producto_id: str, cantidad: int,
                            motivo: MotivoNecesidad, usuario: str,
                            necesidad_id: Optional[str] = None) -> SolicitudDeCompra:
        with self._uow() as uow:
            s = self._obtener(uow.solicitudes, solicitud_id, "Solicitud")
            self._obtener(uow.productos, producto_id, "Producto")
            n = NecesidadReposicion(necesidad_id or nuevo_id("NEC"), producto_id, s.sucursal_id,
                                    cantidad, motivo, usuario, self._clock.ahora())
            s.registrar_necesidad(n)
            uow.solicitudes.guardar(s)
            self._auditar(uow, usuario, "REGISTRAR_NECESIDAD", "Necesidad", n.id, "",
                          n.estado.value)
            uow.commit()
        self._publicar(s)
        return s

    def confirmar_necesidad(self, solicitud_id: str, necesidad_id: str, usuario: str, rol: Rol,
                            cantidad: Optional[int] = None) -> SolicitudDeCompra:
        with self._uow() as uow:
            s = self._obtener(uow.solicitudes, solicitud_id, "Solicitud")
            s.confirmar_necesidad(necesidad_id, usuario, rol, cantidad)
            uow.solicitudes.guardar(s)
            self._auditar(uow, usuario, "CONFIRMAR_NECESIDAD", "Necesidad", necesidad_id,
                          "PENDIENTE_REVISION", "CONFIRMADA")
            uow.commit()
        self._publicar(s)
        return s

    def rechazar_necesidad(self, solicitud_id: str, necesidad_id: str, usuario: str,
                           rol: Rol) -> SolicitudDeCompra:
        with self._uow() as uow:
            s = self._obtener(uow.solicitudes, solicitud_id, "Solicitud")
            s.rechazar_necesidad(necesidad_id, usuario, rol)
            uow.solicitudes.guardar(s)
            self._auditar(uow, usuario, "RECHAZAR_NECESIDAD", "Necesidad", necesidad_id,
                          "PENDIENTE_REVISION", "RECHAZADA")
            uow.commit()
        self._publicar(s)
        return s

    def enviar_solicitud(self, solicitud_id: str, usuario: str, rol: Rol) -> SolicitudDeCompra:
        with self._uow() as uow:
            s = self._obtener(uow.solicitudes, solicitud_id, "Solicitud")
            s.enviar(usuario, rol)
            uow.solicitudes.guardar(s)
            self._auditar(uow, usuario, "ENVIAR_SOLICITUD", "SolicitudDeCompra", s.id,
                          "EN_REVISION", s.estado.value)
            uow.commit()
        self._publicar(s)
        return s

    def obtener_solicitud(self, solicitud_id: str) -> SolicitudDeCompra:
        with self._uow() as uow:
            return self._obtener(uow.solicitudes, solicitud_id, "Solicitud")
