# language: es
@US14 @RN-07 @RF-14
Característica: US14 Corrección de datos descriptivos de una venta completada
  Como responsable de farmacia
  quiero autorizar correcciones de datos descriptivos de una venta completada
  para corregir errores sin alterar la operación económica original

  Escenario: Corrección autorizada de observaciones
    Dado una venta COMPLETADA
    Cuando se corrige el campo descriptivo observaciones con motivo, ejecutor y autorizador
    Entonces se conserva el dato original, el nuevo, el motivo, la fecha, el ejecutor y el autorizador

  Escenario: Dato económico no corregible
    Dado una venta COMPLETADA
    Cuando se intenta corregir un campo económico
    Entonces el sistema responde 422 y la venta no cambia

  Escenario: Venta en proceso no admite correcciones
    Dado una venta EN_PROCESO
    Cuando se intenta registrar una corrección
    Entonces el sistema responde 409
