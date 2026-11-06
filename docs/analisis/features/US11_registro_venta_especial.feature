# language: es
@US11 @RF-09 @RF-16 @RNF-04
Característica: US11 Registro digital de ventas especiales
  Como responsable de farmacia
  quiero registrar digitalmente los datos de las ventas especiales
  para facilitar su consulta histórica y reducir la dependencia de documentos físicos

  Escenario: Captura de los datos aplicables
    Dado una venta que requiere receta
    Cuando el responsable registra folio, médico, cédula, paciente, fecha de emisión y resultado
    Entonces el sistema conserva todos los campos y la identidad del responsable

  Escenario: Venta sin medicamentos con receta
    Dado una venta que no contiene medicamentos con receta
    Cuando se intenta registrar una revisión de receta
    Entonces el sistema responde 422
