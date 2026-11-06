# language: es
@US15 @RN-08 @RF-11
Característica: US15 Registro de diferencias de inventario
  Como personal de Almacén
  quiero registrar las diferencias entre la existencia física y la registrada
  para documentar las discrepancias encontradas durante los conteos

  Escenario: Diferencia registrada sin modificar la existencia
    Dado una existencia registrada de 10 piezas
    Cuando Almacén registra un conteo físico de 7
    Entonces se documenta sucursal, producto, lote, ambas cantidades, fecha y responsable
    Y la existencia sigue siendo 10

  Escenario: Conteo sin diferencia
    Dado una existencia registrada de 10 piezas
    Cuando Almacén registra un conteo físico de 10
    Entonces el sistema responde 422
