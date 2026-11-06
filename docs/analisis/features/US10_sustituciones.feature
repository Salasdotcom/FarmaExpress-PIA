# language: es
@US10 @RF-16 @RF-18
Característica: US10 Autorización de sustituciones de medicamentos
  Como responsable de farmacia
  quiero autorizar las sustituciones de medicamentos y registrar su motivo
  para documentar las decisiones tomadas durante la venta

  Escenario: Sustitución autorizada
    Dado una venta EN_PROCESO con 2 piezas de MED-001
    Cuando el responsable de farmacia autoriza sustituir MED-001 por MED-003 con motivo "sin existencia"
    Entonces se registra producto solicitado, alternativa, motivo y responsable
    Y la línea de la venta pasa a MED-003 con la misma cantidad

  Escenario: Ninguna alternativa aceptada
    Dado una venta EN_PROCESO
    Cuando el responsable de farmacia registra que no acepta ninguna alternativa
    Entonces se conserva la decisión con su motivo
    Y la venta no cambia

  Escenario: Sólo el responsable decide
    Dado un usuario CAJERO
    Cuando intenta autorizar una sustitución
    Entonces el sistema responde 403

  Escenario: Venta ya completada
    Dado una venta COMPLETADA
    Cuando se intenta autorizar una sustitución
    Entonces el sistema responde 409 y no se registra nada
