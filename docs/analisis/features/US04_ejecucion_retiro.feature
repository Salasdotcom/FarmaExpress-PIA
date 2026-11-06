# language: es
@US04 @RN-02 @RF-05
Característica: US04 Cantidades identificadas y retiradas de un lote
  Como personal de Almacén
  quiero registrar las cantidades identificadas y retiradas de un lote
  para documentar la ejecución del retiro

  Escenario: Registro de ejecución por sucursal
    Dado un retiro de lote registrado
    Cuando Almacén registra 30 unidades identificadas y 30 retiradas en SUC-01
    Entonces el retiro queda EN_EJECUCION con sucursal, responsable y fecha

  Escenario: Retiradas mayores que identificadas
    Dado un retiro de lote registrado
    Cuando Almacén registra 5 identificadas y 6 retiradas
    Entonces el sistema responde 422

  Escenario: No concluye con unidades en tránsito pendientes
    Dado un retiro con unidades en tránsito pendientes
    Cuando se intenta concluir el retiro
    Entonces el sistema responde 422 (RN-02)
