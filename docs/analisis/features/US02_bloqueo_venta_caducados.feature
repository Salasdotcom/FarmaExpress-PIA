# language: es
@US02 @RN-01 @RF-02 @DS-02
Característica: US02 Bloqueo de venta de productos caducados
  Como cajero
  quiero que el sistema bloquee la venta de productos caducados
  para impedir que se complete una operación con productos que ya no pueden venderse

  Escenario: Venta con producto caducado
    Dado una venta EN_PROCESO con un producto de un lote que caduca hoy
    Cuando el cajero intenta completar la venta
    Entonces el sistema responde 422 con la violación MEDICAMENTO_CADUCADO
    Y la venta sigue EN_PROCESO
    Y la existencia no cambia

  Escenario: Venta con producto vigente
    Dado una venta EN_PROCESO con un producto de un lote vigente y existencia suficiente
    Cuando el cajero completa la venta
    Entonces la venta queda COMPLETADA y se descuenta la existencia
