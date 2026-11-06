# FarmaExpress — PIA Componentes de Lógica de Negocio (Equipo 10)

Sistema de control de existencias, caducidad, lotes, recetas y ajustes para una farmacia multisucursal.

- Repositorio: https://github.com/Salasdotcom/FarmaExpress-PIA
- Despliegue (Swagger en `/docs`): `<URL_DEPLOY>`

## Arquitectura (DDD en capas)
`src/domain` (agregados, Value Objects, Specifications, State Machine, Domain Events, permisos) →
`src/application` (casos de uso, puertos, auditoría) →
`src/infrastructure` (SQLAlchemy, Unit of Work, memoria, seed) →
`src/api` (FastAPI: routers, esquemas, errores, raíz de composición).
Documentación en `docs/`: `BRD.md`, `architecture/` (ADR-01..07, BPMN), `api/openapi.json`, `trazabilidad.md`.

## Ejecución local
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
SEED_DEMO=true uvicorn src.api.main:app --reload       # http://127.0.0.1:8000/docs
```
Sin `DATABASE_URL` usa SQLite en memoria. Con PostgreSQL: `DATABASE_URL=postgresql://usuario:clave@host/bd`.

## API
Identidad por encabezados (MVP): `X-User-Id` y `X-User-Role` = `CAJERO | RESPONSABLE_FARMACIA | ALMACEN | COMPRAS`.

| Código | Significado |
|---|---|
| 200 / 201 | Éxito / creado |
| 400 | Solicitud mal formada (tipos o campos faltantes) |
| 401 | Falta identidad o rol desconocido |
| 403 | El rol no puede ejecutar la acción (p. ej. Almacén autorizando su propio ajuste) |
| 404 | Recurso inexistente |
| 409 | Transición de estado inválida (p. ej. completar una venta cancelada) |
| 422 | Regla de negocio violada (caducado, lote retirado, receta no aceptada, existencia insuficiente…) |

Datos de demostración (`SEED_DEMO=true`, idempotente, fechas relativas a hoy): productos `MED-001..005`,
lotes `LOT-001..006` (normal, próximo, crítico y **caducado hoy**), sucursales `SUC-01` y `SUC-02`.

Ejemplo:
```bash
curl -X POST localhost:8000/ventas -H "X-User-Id: C1" -H "X-User-Role: CAJERO" \
  -H "content-type: application/json" \
  -d '{"sucursal_id":"SUC-01","items":[{"producto_id":"MED-001","cantidad":2,"lote_id":"LOT-001"}]}'
```
Contrato OpenAPI exportado: `python scripts/export_openapi.py` → `docs/api/openapi.json`.

## Pruebas
```bash
ruff check src tests
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```
Las pruebas de aplicación corren contra memoria **y** SQLAlchemy (mismo contrato).

## Docker Compose (DB + App + Tests)
```bash
cp .env.example .env
docker compose up --build                              # db + app en :8000
docker compose --profile test run --rm tests
```

## Regla clave: caducidad (RN-01)
>90 días normal · 11–90 próximo · 1–10 crítico · **hoy = caducidad o posterior → caducado (no vendible)**.
