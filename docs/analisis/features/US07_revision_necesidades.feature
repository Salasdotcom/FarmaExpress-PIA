# language: es
@US07 @RN-04 @RF-07
Característica: US07 Revisión y confirmación de necesidades
  Como responsable de farmacia
  quiero revisar y confirmar las necesidades de reposición
  para determinar qué productos deben solicitarse a Compras

  Escenario: Confirmar necesidad
    Dado una necesidad PENDIENTE_REVISION
    Cuando el responsable de farmacia la confirma con cantidad 35
    Entonces queda CONFIRMADA con cantidad_confirmada 35

  Escenario: Rechazar necesidad
    Dado una necesidad PENDIENTE_REVISION
    Cuando el responsable de farmacia la rechaza
    Entonces queda RECHAZADA y no formará parte de la solicitud

  Escenario: Almacén no puede revisar
    Dado un usuario ALMACEN
    Cuando intenta confirmar una necesidad
    Entonces el sistema responde 403
