# FarmaExpress — PIA Componentes de Lógica de Negocio (Equipo 10)

Sistema de control de existencias, caducidad, lotes, recetas y ajustes para una farmacia multisucursal.

- Repositorio: `<URL_GITHUB>`
- Despliegue (Swagger en `/docs`): `<URL_DEPLOY>`

## Arquitectura
DDD en capas: `src/domain` (agregados, VO, Specifications, State Machine, eventos) → `src/application` (casos de uso, puertos) → `src/infrastructure` (SQLAlchemy, UoW) → `src/api` (FastAPI).
Documentación en `docs/` (BRD, `architecture/` con ADRs, UML, BPMN; `api/` OpenAPI; `trazabilidad.md`).

## Ejecución local
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload      # http://127.0.0.1:8000/docs
```
## Pruebas
```bash
ruff check src tests
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```
## Docker Compose (DB + App + Tests)
```bash
cp .env.example .env
docker compose up --build              # db + app
docker compose --profile test run --rm tests
```
## Regla clave: caducidad (RN-01)
>90 días normal · 11–90 próximo · 1–10 crítico · **hoy = caducidad o posterior → caducado (no vendible)**.
