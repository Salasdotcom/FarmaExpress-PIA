# ADR-08 — Sustituciones, registros especiales, reportes y correcciones

**Estado:** aceptada · **Fecha:** 2026-11-06

## Contexto
Las historias US10, US11, US12, US14 y US18 añaden operaciones que no encajan en el flujo básico de venta.

## Decisiones
1. **Sustitución (US10)** es una entidad propia (`SustitucionDeVenta`, estados AUTORIZADA/RECHAZADA) y no un campo de la venta: conserva el motivo y al responsable, y un rechazo no modifica la venta. Sólo el responsable de farmacia autoriza.
2. **Registros especiales (US11/US12)** se derivan de la venta y su receta (sin duplicar datos). El cajero nunca ve datos personales; consultas del responsable se auditan (RF-16).
3. **Reportes (US18)** son sólo lectura en `ReporteService`, con filtros comunes y permisos por rol (responsable, almacén, compras); sin datos personales en ventas especiales.
4. **Corrección (US14)** sólo toca datos descriptivos (`observaciones`) de ventas COMPLETADAS, conserva el valor original en `Venta.correcciones` y emite `VentaCorregida`; nunca altera total ni inventario (RN-07).
5. Elegibilidad (`puede_procesarse`, `beneficio_referencia`) se modela con Specifications combinables (AND/OR/NOT), igual que ADR-05.

## Consecuencias
Más tablas (`sustituciones`) creadas por `create_all`; no requieren migración manual. Cada decisión tiene prueba unitaria (memoria y SQL) y de API.
