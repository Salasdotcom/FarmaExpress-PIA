# language: es
@US01 @RN-01 @RF-01
Característica: US01 Clasificación de caducidad
  Como personal de Almacén
  quiero consultar la clasificación de caducidad de los productos
  para identificar cuáles requieren atención prioritaria

  Escenario: Producto normal
    Dado un lote que caduca dentro de 91 días
    Cuando el sistema calcula los días restantes
    Entonces lo clasifica como NORMAL

  Escenario: Producto próximo a caducar
    Dado un lote que caduca dentro de 45 días
    Cuando el sistema calcula los días restantes
    Entonces lo clasifica como PROXIMO_A_CADUCAR

  Escenario: Producto crítico
    Dado un lote que caduca dentro de 7 días
    Cuando el sistema calcula los días restantes
    Entonces lo clasifica como CRITICO

  Escenario: Producto caducado el mismo día
    Dado un lote cuya fecha de caducidad es hoy
    Cuando el sistema calcula los días restantes
    Entonces lo clasifica como CADUCADO y no es vendible
