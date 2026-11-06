# ADR-06. Stack tecnológico y arquitectura en capas

- **Estado:** Aceptado.
- **Contexto:** Debe ser el stack del curso (U4/U5), reproducible con Docker Compose y desplegable en una plataforma gratuita.
- **Decisión:** Python 3.11+, FastAPI (OpenAPI/Swagger automático), SQLAlchemy 2, PostgreSQL (SQLite en memoria para pruebas rápidas), pytest + pytest-cov (≥80%), ruff, Docker Compose (db + app + tests), GitHub Actions, despliegue en Render. Configuración por variables de entorno (12-Factor).
- **Capas:** `domain` (sin dependencias externas) ← `application` (casos de uso, puertos) ← `infrastructure` (adaptadores) y `api` (controladores). El dominio no importa SQLAlchemy ni FastAPI.
- **Consecuencias:** (+) dominio probado sin DB; (+) repositorios intercambiables (SOLID-D); (−) SQLite no reproduce todo PostgreSQL, por eso el CI/compose incluye pruebas contra el motor real cuando sea viable.
