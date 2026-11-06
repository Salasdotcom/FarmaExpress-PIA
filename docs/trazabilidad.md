# Trazabilidad (US → regla → componente → prueba)

| US | Regla / RF | Componente | Prueba |
|---|---|---|---|
| US01 | RN-01, RF-01 | `value_objects.clasificar_caducidad`, `Lote.clasificacion` | `test_caducidad.py`, `test_existencia_lote.py` |
| US02 | RN-01, RF-02 | `SinMedicamentoCaducado`, `ServicioDeValidacionDeVenta` (DS-02) | `test_validacion_venta.py::test_ds02_*` |
| US03 | RN-02, RF-03, RF-04 | `SinLoteRetirado`, `RetiroDeLote.registrar`, `Lote.marcar_retirado` | `test_validacion_venta.py::test_lote_retirado_*`, `test_retiro.py` |
| US04 | RN-02, RF-05 | `RetiroDeLote.registrar_ejecucion`, `concluir` (en tránsito pendiente) | `test_retiro.py` |
| US06-US07 | RN-04, RF-07 | `NecesidadReposicion`, `SolicitudDeCompra.confirmar/rechazar_necesidad` | `test_solicitud_compra.py` |
| US08 | RN-04, RF-07, RF-17 | `SolicitudDeCompra.enviar` (sólo confirmadas) | `test_solicitud_compra.py` |
| US09 | RN-05, RF-08 | `Venta.registrar_revision_receta`, `RecetaAceptada` | `test_venta.py`, `test_validacion_venta.py` |
| US13 | RN-07 | `Venta` (state machine, `TRANSICIONES`) | `test_venta.py::test_transiciones_*` |
| US14 | RN-07, RF-14 | `Venta.corregir_dato_descriptivo` | `test_venta.py::test_correccion_*` |
| US15 | RN-08, RF-11 | `DiferenciaDeInventario.registrar` | `test_diferencia_ajuste.py` |
| US16 | RN-08, RF-12 | `DiferenciaDeInventario.registrar_investigacion` | `test_diferencia_ajuste.py` |
| US17 | RN-09, RF-13 | `AjusteDeInventario` (autorizar ≠ ejecutor, aplicar sólo si AUTORIZADO) | `test_diferencia_ajuste.py` |
| US05 | RN-03, RF-06 | `InventarioApplicationService.consultar_existencias` (informativa, sin reserva) | `test_app_inventario_reposicion.py::test_consulta_*` |
| US02/US09 (caso de uso) | RN-01, RN-05 | `VentaApplicationService.completar_venta` (DS-01, rollback DS-02) | `test_app_venta.py` |
| RF-16 (auditoría) | RF-16 | `IAuditoria`, `RegistroAuditoria`, `_auditar` | `test_app_venta.py::test_ds01_*` |
| Persistencia | ADR-07, RF-16 | `models.py`, `repositories.py`, `SqlAlchemyUnitOfWork`, tabla `historial` | `test_sql_persistencia.py`; `test_app_*.py` corren contra memoria y SQL |
| API REST | RNF-01, US01-US17 | `src/api/routers/*`, `deps.py` (roles), `errors.py` (400/401/403/404/409/422) | `tests/integration/test_api.py` |
| US01 (HTTP) | RN-01 | `GET /lotes/{id}/caducidad` | `test_api.py::test_caducidad_por_lote` |
| US02 (HTTP) | RN-01, DS-02 | `POST /ventas/{id}/completar` → 422 `MEDICAMENTO_CADUCADO` | `test_api.py::test_ds02_*` |
| US03/US04 (HTTP) | RN-02 | `POST /lotes/{id}/retiro`, `/retiros/{id}/*` | `test_api.py::test_retiro_*`, `test_lote_retirado_*` |
| US17 (HTTP) | RN-09, ADR-02 | `POST /ajustes/{id}/autorizar` → 403 si autoriza el ejecutor | `test_api.py::test_ajuste_flujo_*` |
| RF-16 (HTTP) | RF-16, RNF-01 | `GET /auditoria` (sólo responsable) | `test_api.py::test_auditoria_*` |
| Pendiente | US10-US12, US18 | — | — |

## Adaptación de fixtures de la maestra
Los CSV (actores/catálogo/operaciones) usan un modelo genérico de pedidos. Mapeo: `catalogo` → Producto+Existencia; `operaciones` → Venta (CREADO→EN_PROCESO); `detalle_operaciones` → LineaDeVenta. Faltan lote/caducidad/sucursal/receta: se genera seed propio. (Completar en Fase 4.)

## Fase 4 — paquete de pruebas del docente
| Requisito del PIA | Regla | Componente | Prueba |
|---|---|---|---|
| ≥3 Specifications con AND/OR/NOT | `puede_procesarse`, `beneficio_referencia` | `src/domain/elegibilidad.py` | `test_fixtures_docente.py::test_composicion_and_or_not`, 120 casos parametrizados |
| Total con Decimal | total = Σ precio × cantidad | `fixtures_csv.total_de`, `Dinero` | `test_total_exacto_con_decimal` |
| Transiciones válidas/ inválidas con evento o excepción | State Machine de `Venta` | `venta.py`, `venta_service.py` | `test_completar_cancelar_y_eventos`, `test_repetir_aprobacion_y_saltar_estado_son_invalidas` |
| Evidencia por caso | — | `scripts/ejecutar_fixtures.py` | `docs/evidencia/*.csv`, `test_script_genera_evidencia_sin_pendientes` |
