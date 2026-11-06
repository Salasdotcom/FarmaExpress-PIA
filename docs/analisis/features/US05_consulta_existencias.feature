# language: es
@US05 @RN-03 @RF-06
Característica: US05 Consulta de existencias de otras sucursales
  Como personal autorizado
  quiero consultar las existencias registradas de otras sucursales
  para conocer dónde aparece disponibilidad de un producto

  Escenario: Existencias por sucursal sin reservas
    Dado un usuario autenticado
    Cuando busca un producto
    Entonces el sistema muestra las cantidades por sucursal y lote
    Y no genera reservas ni transferencias, la consulta es informativa

  Escenario: Usuario sin identificar
    Dado una solicitud sin encabezados de identidad
    Cuando consulta existencias
    Entonces el sistema responde 401
