# language: es
@US18 @RF-15 @RNF-01 @RNF-08
Característica: US18 Reportes operativos filtrados
  Como responsable de farmacia
  quiero generar reportes operativos filtrados por los datos pertinentes
  para facilitar la supervisión y la toma de decisiones

  Escenario: Reporte de caducidad filtrado por estado
    Dado lotes con distintas fechas de caducidad
    Cuando el usuario autorizado solicita el reporte de caducidad con estado CADUCADO
    Entonces el sistema presenta sólo los lotes caducados ordenados por días restantes

  Escenario: Filtros por sucursal, producto, lote, estado y periodo
    Dado registros de retiros, diferencias, ajustes, solicitudes y ventas especiales
    Cuando el usuario aplica los filtros que correspondan a cada reporte
    Entonces el sistema presenta la información disponible que cumple los filtros

  Escenario: Reporte de ventas especiales sin datos personales
    Dado ventas especiales registradas
    Cuando se solicita el reporte ventas_especiales
    Entonces las filas no incluyen paciente, médico ni cédula

  Escenario: Permisos
    Dado un usuario CAJERO
    Cuando solicita cualquier reporte
    Entonces el sistema responde 403
