# FarmaExpress — PIA Componentes de Lógica de Negocio (Equipo 10)

Sistema de control de existencias, caducidad, lotes, recetas y ajustes para una farmacia multisucursal.

- Repositorio: https://github.com/Salasdotcom/FarmaExpress-PIA
- Despliegue (Swagger en `/docs`): https://farmaexpress-api-0qfl.onrender.com/docs

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


## Uso desde Swagger UI (formularios)

Todos los POST reciben **formularios** (un recuadro por campo; los opcionales pueden dejarse en
blanco) y el rol se elige de una lista. Cada respuesta 200/201 incluye un campo `mensaje` que
explica qué ocurrió; las 422 de venta incluyen `violaciones` y `explicacion` legible.

## Paquete de pruebas del docente (Fase 4)
`python scripts/ejecutar_fixtures.py` ejecuta los 120 casos y 20 transiciones y deja la evidencia en
`docs/evidencia/`. Mapeo y diferencias: [docs/fixtures_mapeo.md](docs/fixtures_mapeo.md).


## Despliegue en Render (producción para la demo)
1. Repositorio en GitHub con `render.yaml` en la raíz.
2. En Render: **New → Blueprint** → elegir el repositorio → *Apply*. Crea la API (Docker) y la
   base PostgreSQL `farmaexpress-db`; `DATABASE_URL` se inyecta automáticamente.
3. Al terminar, Swagger UI queda en `https://<servicio>.onrender.com/docs` y el contrato en
   `/openapi.json`. Variables: `DATABASE_URL`, `APP_ENV=production`, `SEED_DEMO=true`.
4. El plan gratuito duerme tras 15 min sin tráfico: abrir `/health` un minuto antes de la demo.

## Docker Compose (DB + App + Tests)
```
copy .env.example .env          # PowerShell: Copy-Item .env.example .env
docker compose up --build       # PostgreSQL 16 + API en http://localhost:8000/docs
docker compose --profile test run --rm tests   # ruff + pytest con cobertura >= 80 %
docker compose down -v          # apagar y borrar el volumen
```
