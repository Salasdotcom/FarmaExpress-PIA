# language: es
@US08 @RN-04 @RF-07 @RF-17
Característica: US08 Registro y envío de solicitudes de compra
  Como responsable de farmacia
  quiero registrar y enviar solicitudes de compra a Compras
  para dar seguimiento a las necesidades de abastecimiento

  Escenario: Envío sólo de lo confirmado
    Dado una solicitud con una necesidad confirmada y otra rechazada
    Cuando el responsable de farmacia la envía
    Entonces la solicitud queda ENVIADA con fecha de envío y solicitante
    Y sólo incluye los productos confirmados

  Escenario: Necesidades pendientes impiden el envío
    Dado una solicitud con una necesidad pendiente de revisión
    Cuando se intenta enviar
    Entonces el sistema responde 422

  Escenario: Solicitud enviada no admite cambios
    Dado una solicitud ENVIADA
    Cuando se intenta registrar otra necesidad
    Entonces el sistema responde 409
