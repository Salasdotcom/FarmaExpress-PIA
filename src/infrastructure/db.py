"""Configuración de base de datos (12-Factor: todo viene de DATABASE_URL)."""
import os
from typing import Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

URL_POR_DEFECTO = "sqlite+pysqlite:///:memory:"


def normalizar_url(url: str) -> str:
    """Render/Heroku entregan 'postgres://'; SQLAlchemy exige 'postgresql://'."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def crear_engine(url: Optional[str] = None) -> Engine:
    url = normalizar_url(url or os.getenv("DATABASE_URL") or URL_POR_DEFECTO)
    if url.startswith("sqlite"):
        opciones: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url or url.rstrip("/").endswith("sqlite+pysqlite:"):
            opciones["poolclass"] = StaticPool  # una sola conexión para toda la BD en memoria
        return create_engine(url, **opciones)
    return create_engine(url, pool_pre_ping=True)


def crear_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    from src.infrastructure.models import Base
    Base.metadata.create_all(engine)
