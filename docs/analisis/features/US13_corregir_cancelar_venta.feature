# language: es
@US13 @RN-07
Característica: US13 Corregir o cancelar una venta en proceso
  Como cajero
  quiero corregir o cancelar una venta en proceso antes de completar el pago
  para solucionar errores o atender el abandono de una operación

  Escenario: Agregar producto a venta en proceso
    Dado una venta EN_PROCESO
    Cuando el cajero agrega un producto
    Entonces la venta conserva el estado EN_PROCESO con la nueva línea y el total actualizado

  Escenario: Cancelar venta en proceso
    Dado una venta EN_PROCESO
    Cuando el cajero la cancela con un motivo
    Entonces queda CANCELADA y el inventario no cambia

  Escenario: Venta cancelada no se completa
    Dado una venta CANCELADA
    Cuando se intenta completar
    Entonces el sistema responde 409
