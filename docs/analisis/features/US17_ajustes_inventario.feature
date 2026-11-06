# language: es
@US17 @RN-09 @RF-13 @ADR-02
Característica: US17 Autorización de ajustes de inventario
  Como responsable de farmacia
  quiero autorizar los ajustes de inventario y conservar su historial
  para asegurar que las correcciones estén justificadas y puedan auditarse

  Escenario: Flujo solicitar, autorizar y aplicar
    Dado una diferencia con causa y evidencia
    Cuando Almacén solicita el ajuste, el responsable lo autoriza y Almacén lo aplica
    Entonces la existencia cambia sólo al aplicar
    Y se conservan cantidad anterior, nueva, motivo, evidencia, fecha, ejecutor y autorizador

  Escenario: Almacén no autoriza su propio ajuste
    Dado un ajuste solicitado por Almacén
    Cuando el mismo usuario o un usuario ALMACEN intenta autorizarlo
    Entonces el sistema responde 403

  Escenario: No se aplica un ajuste sin autorizar
    Dado un ajuste PENDIENTE
    Cuando se intenta aplicar
    Entonces el sistema responde 409
