# ADR-04. State Machine explícita para los agregados con ciclo de vida

- **Estado:** Aceptado.
- **Contexto:** Venta, Ajuste, Necesidad de reposición y Retiro de lote cambian de estado y varias reglas dependen de ello (RN-07: una venta completada no se modifica; RN-09: un ajuste no se aplica sin autorización). Evitar `if` dispersos por los servicios.
- **Alternativas:** (a) condiciones `if estado == ...` en cada operación; (b) patrón State con una clase por estado; (c) tabla de transiciones explícita dentro del agregado.
- **Decisión:** Tabla de transiciones por agregado (`TRANSICIONES` en `src/domain/venta.py`). Toda transición pasa por un único método que valida y lanza `InvalidTransition` (HTTP 409). El evento de dominio se registra solo después de una transición válida.
- **Consecuencias:** (+) reglas visibles y probables con una prueba parametrizada; (+) transiciones inválidas no dejan eventos ni cambios parciales; (−) agregar estados exige editar la tabla (aceptable: son pocos y estables).
- **Estados:** Venta `EN_PROCESO→COMPLETADA|CANCELADA`; Ajuste `PENDIENTE→AUTORIZADO→APLICADO` (+`RECHAZADO`); Necesidad `PENDIENTE_REVISION→CONFIRMADA|RECHAZADA`; Retiro `REGISTRADO→EN_EJECUCION→EJECUTADO`.
- **Trazabilidad:** US02, US09, US13, US14, US17; RN-05, RN-07, RN-09; `tests/unit/test_venta.py`.
