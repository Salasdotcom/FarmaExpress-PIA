# language: es
@US06 @RN-04 @RF-07
Característica: US06 Registro de necesidades de reposición
  Como personal de Almacén
  quiero registrar productos faltantes o que requieren reposición
  para informar las necesidades de abastecimiento

  Escenario: Necesidad registrada pendiente de revisión
    Dado una solicitud de compra EN_REVISION de SUC-01
    Cuando Almacén registra una necesidad FALTANTE de 20 unidades
    Entonces la necesidad queda PENDIENTE_REVISION con fecha y registrante
    Y no se genera ningún pedido automático

  Escenario: Cantidad inválida
    Dado una solicitud de compra EN_REVISION de SUC-01
    Cuando Almacén registra una necesidad con cantidad 0
    Entonces el sistema responde 422
