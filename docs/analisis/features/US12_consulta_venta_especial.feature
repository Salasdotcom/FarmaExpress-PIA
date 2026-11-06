# language: es
@US12 @RF-10 @RNF-01 @RNF-04 @RNF-06
Característica: US12 Consulta de registros de venta especial según permisos
  Como usuario autorizado
  quiero consultar los registros de venta especial según mis permisos
  para recuperar la información necesaria para las actividades de la farmacia

  Escenario: Responsable de farmacia
    Dado registros de venta especial existentes
    Cuando el responsable de farmacia los consulta
    Entonces ve todos los datos, incluidos paciente, médico y cédula
    Y la consulta queda auditada

  Escenario: Cajero
    Dado registros de venta especial existentes
    Cuando el cajero los consulta
    Entonces ve el folio y el resultado pero no paciente, médico ni cédula

  Escenario: Almacén y Compras
    Dado registros de venta especial existentes
    Cuando un usuario ALMACEN o COMPRAS intenta consultarlos
    Entonces el sistema responde 403
