# language: es
@US16 @RN-08 @RF-12
Característica: US16 Investigación de diferencias de inventario
  Como responsable de farmacia
  quiero documentar la investigación de una diferencia de inventario
  para identificar su causa o mantener constancia de que sigue pendiente

  Escenario: Causa identificada con evidencia
    Dado una diferencia registrada
    Cuando se documenta la causa "error de captura" y la evidencia "conteo ciego"
    Entonces la diferencia queda con causa identificada y es ajustable

  Escenario: Pendiente de aclaración
    Dado una diferencia registrada
    Cuando la investigación no determina causa
    Entonces la diferencia queda PENDIENTE_ACLARACION y no es ajustable
