"""Identidad y permisos por encabezado (MVP de RNF-01). En producción se sustituiría por JWT."""
from dataclasses import dataclass
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request

from src.api.container import Container
from src.domain.permisos import exigir_rol
from src.domain.value_objects import Rol


@dataclass(frozen=True)
class Usuario:
    id: str
    rol: Rol


def get_container(request: Request) -> Container:
    return request.app.state.container


def usuario_actual(
    x_user_id: Annotated[Optional[str], Header(description="Identificador del usuario")] = None,
    x_user_role: Annotated[Optional[str], Header(
        description="CAJERO | RESPONSABLE_FARMACIA | ALMACEN | COMPRAS")] = None,
) -> Usuario:
    if not x_user_id or not x_user_role:
        raise HTTPException(401, "Faltan los encabezados X-User-Id y X-User-Role")
    try:
        return Usuario(x_user_id, Rol(x_user_role.upper()))
    except ValueError:
        raise HTTPException(401, f"Rol desconocido: {x_user_role}") from None


def con_roles(*permitidos: Rol):
    """Dependencia que exige que el usuario tenga uno de los roles (si no, 403)."""
    def dependencia(usuario: Annotated[Usuario, Depends(usuario_actual)]) -> Usuario:
        exigir_rol(usuario.rol, *permitidos)
        return usuario
    return dependencia


CAJERO, RF, ALMACEN, COMPRAS = (Rol.CAJERO, Rol.RESPONSABLE_FARMACIA, Rol.ALMACEN, Rol.COMPRAS)
Cont = Annotated[Container, Depends(get_container)]
Autenticado = Annotated[Usuario, Depends(usuario_actual)]
EnVentas = Annotated[Usuario, Depends(con_roles(CAJERO, RF))]
SoloRF = Annotated[Usuario, Depends(con_roles(RF))]
EnInventario = Annotated[Usuario, Depends(con_roles(ALMACEN, RF))]
