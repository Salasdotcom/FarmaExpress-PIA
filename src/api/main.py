import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from src.api.container import Container, build_container
from src.api.errors import registrar_errores
from src.api.routers import (
    auditoria,
    inventario,
    registros_especiales,
    reportes,
    reposicion,
    ventas,
)
from src.infrastructure.db import init_db
from src.infrastructure.seed import cargar_demo

DESCRIPCION = """
Lógica de negocio de **FarmaExpress** (PIA, Componentes de Lógica de Negocio).

**Autenticación (MVP):** envíe `X-User-Id` y `X-User-Role`
(`CAJERO`, `RESPONSABLE_FARMACIA`, `ALMACEN`, `COMPRAS`).

**Códigos:** 200/201 éxito · 400 solicitud mal formada · 401 sin identidad ·
403 rol sin permiso · 404 no existe · 409 transición de estado inválida ·
422 regla de negocio violada.
"""


def create_app(container: Optional[Container] = None, seed: Optional[bool] = None) -> FastAPI:
    contenedor = container or build_container()
    if seed is None:
        seed = os.getenv("SEED_DEMO", "").lower() in ("1", "true", "yes")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        init_db(contenedor.engine)
        if seed:
            cargar_demo(contenedor.uow_factory, contenedor.clock)
        yield
        if container is None:
            contenedor.engine.dispose()

    app = FastAPI(title="FarmaExpress API", version="1.0.0", description=DESCRIPCION,
                  lifespan=lifespan)
    app.state.container = contenedor
    registrar_errores(app)
    for r in (ventas.router, registros_especiales.router, inventario.router, reposicion.router,
              reportes.router, auditoria.router):
        app.include_router(r)

    @app.get("/health", tags=["infra"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
