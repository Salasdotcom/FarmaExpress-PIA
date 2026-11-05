# Trazabilidad (US → regla → componente → prueba)

| US | Regla / RF | Componente | Prueba |
|---|---|---|---|
| US01 | RN-01, RF-01 | `value_objects.clasificar_caducidad`, `Lote.clasificacion` | `test_caducidad.py`, `test_existencia_lote.py` |
| US02 | RN-01, RF-02 | `SinMedicamentoCaducado`, `ServicioDeValidacionDeVenta` (DS-02) | `test_validacion_venta.py::test_ds02_*` |
| US03 | RN-02, RF-04 | `SinLoteRetirado`, `Lote.marcar_retirado` | `test_validacion_venta.py::test_lote_retirado_*` |
| US09 | RN-05, RF-08 | `Venta.registrar_revision_receta`, `RecetaAceptada` | `test_venta.py`, `test_validacion_venta.py` |
| US13 | RN-07 | `Venta` (state machine, `TRANSICIONES`) | `test_venta.py::test_transiciones_*` |
| US14 | RN-07, RF-14 | `Venta.corregir_dato_descriptivo` | `test_venta.py::test_correccion_*` |
| Pendiente | US04–US08, US10–US12, US15–US18 | — | — |

## Adaptación de fixtures de la maestra
Los CSV (actores/catálogo/operaciones) usan un modelo genérico de pedidos. Mapeo: `catalogo` → Producto+Existencia; `operaciones` → Venta (CREADO→EN_PROCESO); `detalle_operaciones` → LineaDeVenta. Faltan lote/caducidad/sucursal/receta: se genera seed propio. (Completar en Fase 4.)
