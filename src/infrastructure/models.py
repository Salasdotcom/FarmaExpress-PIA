"""Modelos de persistencia (ORM). Son independientes de las clases del dominio (ADR-07):
los repositorios traducen entre ambos."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Money(TypeDecorator):
    """Decimal exacto: NUMERIC en PostgreSQL; texto en SQLite (que no tiene decimales)."""
    impl = Numeric(12, 2)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(32))
        return dialect.type_descriptor(Numeric(12, 2))

    def process_bind_param(self, value, dialect):
        if value is None or dialect.name != "sqlite":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        return None if value is None else Decimal(str(value))


class UTCDateTime(TypeDecorator):
    """Guarda UTC y siempre devuelve datetimes con zona horaria."""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        return None if value is None else value.replace(tzinfo=timezone.utc)


class Base(DeclarativeBase):
    pass


class ProductoRow(Base):
    __tablename__ = "productos"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    descripcion: Mapped[str] = mapped_column(String(200))
    precio: Mapped[Decimal] = mapped_column(Money)
    categoria: Mapped[str] = mapped_column(String(32))
    habilitado: Mapped[bool] = mapped_column(Boolean, default=True)


class LoteRow(Base):
    __tablename__ = "lotes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    producto_id: Mapped[str] = mapped_column(String(64), index=True)
    fecha_caducidad: Mapped[date] = mapped_column(Date)
    retirado: Mapped[bool] = mapped_column(Boolean, default=False)


class ExistenciaRow(Base):
    __tablename__ = "existencias"
    clave: Mapped[str] = mapped_column(String(200), primary_key=True)
    producto_id: Mapped[str] = mapped_column(String(64), index=True)
    lote_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sucursal_id: Mapped[str] = mapped_column(String(64))
    cantidad: Mapped[int] = mapped_column(Integer)


class VentaRow(Base):
    __tablename__ = "ventas"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sucursal_id: Mapped[str] = mapped_column(String(64))
    cajero_id: Mapped[str] = mapped_column(String(64))
    estado: Mapped[str] = mapped_column(String(20))
    observaciones: Mapped[str] = mapped_column(Text, default="")
    correcciones: Mapped[list] = mapped_column(JSON, default=list)
    receta_folio: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    receta_medico: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    receta_cedula: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    receta_paciente: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    receta_fecha: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    receta_resultado: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    receta_revisada_por: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    lineas: Mapped[list["LineaVentaRow"]] = relationship(
        cascade="all, delete-orphan", order_by="LineaVentaRow.orden", lazy="selectin")


class LineaVentaRow(Base):
    __tablename__ = "lineas_venta"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id: Mapped[str] = mapped_column(ForeignKey("ventas.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    producto_id: Mapped[str] = mapped_column(String(64))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[Decimal] = mapped_column(Money)
    lote_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    requiere_receta: Mapped[bool] = mapped_column(Boolean, default=False)


class RetiroRow(Base):
    __tablename__ = "retiros"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lote_id: Mapped[str] = mapped_column(String(64))
    producto_id: Mapped[str] = mapped_column(String(64))
    motivo: Mapped[str] = mapped_column(Text)
    registrado_por: Mapped[str] = mapped_column(String(64))
    estado: Mapped[str] = mapped_column(String(20))
    en_transito_pendiente: Mapped[int] = mapped_column(Integer, default=0)
    ejecuciones: Mapped[list["EjecucionRow"]] = relationship(
        cascade="all, delete-orphan", order_by="EjecucionRow.orden", lazy="selectin")


class EjecucionRow(Base):
    __tablename__ = "retiro_ejecuciones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retiro_id: Mapped[str] = mapped_column(ForeignKey("retiros.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    sucursal_id: Mapped[str] = mapped_column(String(64))
    identificadas: Mapped[int] = mapped_column(Integer)
    retiradas: Mapped[int] = mapped_column(Integer)
    responsable_id: Mapped[str] = mapped_column(String(64))
    fecha: Mapped[datetime] = mapped_column(UTCDateTime)


class DiferenciaRow(Base):
    __tablename__ = "diferencias"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    producto_id: Mapped[str] = mapped_column(String(64))
    sucursal_id: Mapped[str] = mapped_column(String(64))
    lote_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cantidad_registrada: Mapped[int] = mapped_column(Integer)
    cantidad_fisica: Mapped[int] = mapped_column(Integer)
    fecha_conteo: Mapped[datetime] = mapped_column(UTCDateTime)
    usuario_responsable: Mapped[str] = mapped_column(String(64))
    prioritaria: Mapped[bool] = mapped_column(Boolean, default=False)
    estado: Mapped[str] = mapped_column(String(30))
    causa_identificada: Mapped[str] = mapped_column(Text, default="")
    evidencia: Mapped[str] = mapped_column(Text, default="")
    investigador_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class AjusteRow(Base):
    __tablename__ = "ajustes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    diferencia_id: Mapped[str] = mapped_column(String(64))
    producto_id: Mapped[str] = mapped_column(String(64))
    lote_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sucursal_id: Mapped[str] = mapped_column(String(64))
    cantidad_anterior: Mapped[int] = mapped_column(Integer)
    cantidad_nueva: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str] = mapped_column(Text)
    evidencia: Mapped[str] = mapped_column(Text, default="")
    ejecutor_id: Mapped[str] = mapped_column(String(64))
    fecha: Mapped[datetime] = mapped_column(UTCDateTime)
    estado: Mapped[str] = mapped_column(String(20))
    autorizador_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class SolicitudRow(Base):
    __tablename__ = "solicitudes_compra"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    sucursal_id: Mapped[str] = mapped_column(String(64))
    estado: Mapped[str] = mapped_column(String(20))
    solicitante_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    fecha_envio: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    necesidades: Mapped[list["NecesidadRow"]] = relationship(
        cascade="all, delete-orphan", order_by="NecesidadRow.orden", lazy="selectin")


class NecesidadRow(Base):
    __tablename__ = "necesidades_reposicion"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    solicitud_id: Mapped[str] = mapped_column(ForeignKey("solicitudes_compra.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    producto_id: Mapped[str] = mapped_column(String(64))
    sucursal_id: Mapped[str] = mapped_column(String(64))
    cantidad_requerida: Mapped[int] = mapped_column(Integer)
    motivo: Mapped[str] = mapped_column(String(30))
    registrada_por: Mapped[str] = mapped_column(String(64))
    fecha: Mapped[datetime] = mapped_column(UTCDateTime)
    estado: Mapped[str] = mapped_column(String(30))
    cantidad_confirmada: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    revisada_por: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class HistorialRow(Base):
    """Bitácora de auditoría (RF-16). Sólo se inserta; nunca se modifica."""
    __tablename__ = "historial"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario: Mapped[str] = mapped_column(String(64))
    accion: Mapped[str] = mapped_column(String(50), index=True)
    entidad: Mapped[str] = mapped_column(String(50))
    entidad_id: Mapped[str] = mapped_column(String(64), index=True)
    antes: Mapped[str] = mapped_column(Text, default="")
    despues: Mapped[str] = mapped_column(Text, default="")
    fecha: Mapped[datetime] = mapped_column(UTCDateTime)
