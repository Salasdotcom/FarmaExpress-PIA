# Modelos BPMN de FarmaExpress

| Proceso | Descripción | Historias | Archivo |
|---|---|---|---|
| PM-01 / PM-06 | Proceso de venta y subproceso de producto no vendible | US01–US04 | `FarmaExpress_BPMN.svg` (páginas 1 y 2, draw.io) |
| PM-04 / PM-05 | Reposición reactiva | US07–US09 | `FarmaExpress_BPMN.svg` (página 3, draw.io) |
| PM-02 | Retiro de lotes | US06 | `PM-02_retiro_lotes.bpmn/.svg` |
| PM-03 | Consulta de existencias entre sucursales | US05 | `PM-03_consulta_existencias.bpmn/.svg` |
| PM-07 | Sustitución de medicamento | US10 | `PM-07_sustitucion.bpmn/.svg` |
| PM-08 | Ventas especiales (registros) | US11, US12 | `PM-08_ventas_especiales.bpmn/.svg` |
| PM-09 | Investigación de diferencias de inventario | US15, US16 | `PM-09_diferencias_inventario.bpmn/.svg` |
| PM-10 | Ajustes de inventario | US16, US17 | `PM-10_ajustes_inventario.bpmn/.svg` |
| PM-11 | Generación de reportes operativos | US18 | `PM-11_reportes.bpmn/.svg` |
| PM-12 | Corrección de datos descriptivos de una venta | US14 | `PM-12_correccion_venta.bpmn/.svg` |

Los `.bpmn` (BPMN 2.0 con DI) abren en bpmn.io o Camunda Modeler; los `.svg` se ven en cualquier navegador.
Los PM-02…PM-12 se generan con `python scripts/generar_bpmn.py`.
