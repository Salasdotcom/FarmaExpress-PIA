# ADR-05. Specification pattern para las reglas de venta

- **Estado:** Aceptado.
- **Contexto:** Completar una venta exige varias condiciones (no caducado, lote no retirado, existencias suficientes, receta aceptada si aplica). Deben combinarse, reutilizarse y reportar cuál falló.
- **Alternativas:** (a) una función con muchos `if`; (b) validadores encadenados; (c) Specifications componibles con `&`, `|` y `~`.
- **Decisión:** Specifications en `src/domain/specifications.py`, cada una con un `codigo` de violación. `ServicioDeValidacionDeVenta` las compone y devuelve todas las violaciones (flujos DS-01 y DS-02). Ejemplo: `SinRecetaRequerida() | RecetaAceptada()`.
- **Consecuencias:** (+) reglas aisladas, probadas una a una y componibles; (+) agregar una regla no modifica las existentes (OCP); (−) más clases pequeñas.
- **Trazabilidad:** US02, US03, US09; RN-01, RN-02, RN-05; `tests/unit/test_validacion_venta.py`.
