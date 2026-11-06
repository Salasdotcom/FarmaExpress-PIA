# language: es
@US09 @RN-05 @RF-08
Característica: US09 Revisión de receta
  Como cajero
  quiero registrar el resultado de la revisión de una receta
  para saber si la venta puede continuar conforme al procedimiento aplicable

  Escenario: Medicamento con receta sin revisar
    Dado una venta con un medicamento que requiere receta y sin revisión
    Cuando el cajero intenta completar la venta
    Entonces el sistema responde 422 con RECETA_REQUERIDA

  Escenario: Receta incompleta
    Dado que el responsable de farmacia registra la revisión con resultado INCOMPLETA
    Cuando el cajero intenta completar la venta
    Entonces el sistema responde 422 con RECETA_NO_ACEPTADA

  Escenario: Receta aceptada
    Dado que el responsable de farmacia registra la revisión con resultado ACEPTADA
    Cuando el cajero completa la venta
    Entonces la venta queda COMPLETADA y la revisión conserva al responsable

  Escenario: El cajero no revisa recetas
    Dado un usuario CAJERO
    Cuando intenta registrar la revisión de una receta
    Entonces el sistema responde 403
