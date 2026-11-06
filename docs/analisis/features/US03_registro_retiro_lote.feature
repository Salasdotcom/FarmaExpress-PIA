# language: es
@US03 @RN-02 @RF-03 @RF-04
Característica: US03 Registro de retiro confirmado de un lote
  Como responsable de farmacia
  quiero registrar el retiro confirmado de un lote
  para detener su comercialización en todas las sucursales

  Escenario: Retiro bloquea el lote en todas las sucursales
    Dado un lote identificado cuyo retiro fue confirmado
    Cuando el responsable de farmacia registra el retiro
    Entonces el lote queda marcado como retirado
    Y cualquier venta con ese lote en cualquier sucursal responde 422 con LOTE_RETIRADO

  Escenario: Sólo el responsable registra retiros
    Dado un usuario con rol ALMACEN
    Cuando intenta registrar el retiro de un lote
    Entonces el sistema responde 403
