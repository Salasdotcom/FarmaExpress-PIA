from src.domain.errors import PermisoDenegado
from src.domain.value_objects import Rol


def exigir_rol(rol: Rol, *permitidos: Rol) -> None:
    if rol not in permitidos:
        nombres = ", ".join(p.value for p in permitidos)
        raise PermisoDenegado(f"Rol {rol.value} sin permiso; requiere {nombres}")
