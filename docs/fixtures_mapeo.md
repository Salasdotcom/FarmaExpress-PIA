# Paquete de pruebas del docente → FarmaExpress (Fase 4)

Las reglas del paquete (`puede_procesarse`, `beneficio_referencia`, estados CREADO→VALIDADO→
PREPARADO→ENTREGADO) son un **modelo de pruebas propuesto**, no el BRD del equipo. Se conservan
los requerimientos propios y se documentan las diferencias.

## Mapeo de datos
| Paquete | FarmaExpress |
|---|---|
| `catalogo.csv` (20 recursos) | `Producto` + `Lote LOT-<id>` (caduca hoy+365) + `Existencia` en SUC-01 con `capacidad_o_stock`; `habilitado=0` → producto no habilitado |
| `operaciones.csv` / `detalle_operaciones.csv` | `Venta` creada vía `VentaApplicationService`; estado inicial **CREADO ≡ EN_PROCESO** |
| `actores.csv` | `OperacionEvaluable` (el comprador no es parte del agregado `Venta`; BRD: el cajero opera) |
| total | `Σ precio_mxn × cantidad` con `Decimal` (`Dinero`) |

## Reglas → Specifications (`src/domain/elegibilidad.py`)
- `puede_procesarse = ActorActivo & OperacionConLineas & OperacionAutorizada`
- `beneficio_referencia = ActorPreferente & TotalMinimo(1500) & ~PromocionActiva`

## Acciones de transición → máquina de estados real
| acción | ejecución | resultado esperado |
|---|---|---|
| completar / aprobar | `completar_venta` (tras `puede_procesarse`) | COMPLETADA + `VentaCompletada`, o excepción de regla (422) |
| cancelar | `cancelar_venta` | CANCELADA + `VentaCancelada` |
| repetir_aprobacion | completar dos veces | 2.ª vez `InvalidTransition` (409) |
| saltar_estado | cancelar y luego completar (nuestro flujo no tiene estados intermedios) | `InvalidTransition` (409) |

## Diferencias respecto al modelo propuesto
1. Estados propios: EN_PROCESO/COMPLETADA/CANCELADA (BRD); no existen VALIDADO/PREPARADO/ENTREGADO.
2. "Autorización" y "cliente activo/preferente" son precondiciones del paquete, no reglas del BRD.
3. Los productos con `habilitado=0` (FAR-P011) se rechazan al crear la venta (422).

## Evidencia
`python scripts/ejecutar_fixtures.py` genera `docs/evidencia/casos_prueba_resultados.csv`
(120 filas) y `transiciones_resultados.csv` (20 filas) con `resultado_alumno` lleno. Las pruebas
`tests/unit/test_fixtures_docente.py` verifican los 120 casos contra un oráculo independiente.
