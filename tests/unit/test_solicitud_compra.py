import pytest

from src.domain.errors import InvalidTransition, PermisoDenegado, ReglaDeNegocioViolada
from src.domain.solicitud_compra import (
    EstadoNecesidad,
    EstadoSolicitud,
    MotivoNecesidad,
    NecesidadReposicion,
    SolicitudDeCompra,
)
from src.domain.value_objects import Rol

RF = Rol.RESPONSABLE_FARMACIA


def nec(id="N1", prod="P1", cant=5, suc="S1"):
    return NecesidadReposicion(id, prod, suc, cant, MotivoNecesidad.FALTANTE, "A1")


def solicitud(*necesidades):
    s = SolicitudDeCompra("SC1", "S1")
    for n in necesidades:
        s.registrar_necesidad(n)
    return s


def test_necesidad_cantidad_invalida():
    with pytest.raises(ReglaDeNegocioViolada):
        nec(cant=0)


def test_registrar_necesidad_queda_pendiente_y_sucursal_coherente():
    s = solicitud(nec())
    assert s.necesidades[0].estado is EstadoNecesidad.PENDIENTE_REVISION
    with pytest.raises(ReglaDeNegocioViolada):
        s.registrar_necesidad(nec("N2", suc="S2"))


def test_flujo_completo_confirmar_rechazar_enviar():
    s = solicitud(nec("N1", "P1", 5), nec("N2", "P2", 3), nec("N3", "P3", 2))
    s.confirmar_necesidad("N1", "RF1", RF)
    s.confirmar_necesidad("N2", "RF1", RF, cantidad=4)  # ajusta la cantidad
    s.rechazar_necesidad("N3", "RF1", RF)
    s.enviar("RF1", RF)
    assert s.estado is EstadoSolicitud.ENVIADA and s.fecha_envio and s.solicitante_id == "RF1"
    assert s.lineas == [("P1", 5), ("P2", 4)]  # lo rechazado no se solicita
    assert s.events[-1].nombre == "SolicitudDeCompraEnviada"


def test_no_se_envia_con_pendientes_o_sin_confirmadas():
    s = solicitud(nec("N1"), nec("N2", "P2"))
    s.confirmar_necesidad("N1", "RF1", RF)
    with pytest.raises(ReglaDeNegocioViolada):
        s.enviar("RF1", RF)  # N2 pendiente
    s.rechazar_necesidad("N2", "RF1", RF)
    s2 = solicitud(nec("N1"))
    s2.rechazar_necesidad("N1", "RF1", RF)
    with pytest.raises(ReglaDeNegocioViolada):
        s2.enviar("RF1", RF)  # ninguna confirmada


def test_solo_responsable_revisa_y_envia():
    s = solicitud(nec())
    with pytest.raises(PermisoDenegado):
        s.confirmar_necesidad("N1", "A1", Rol.ALMACEN)
    with pytest.raises(PermisoDenegado):
        s.rechazar_necesidad("N1", "A1", Rol.ALMACEN)
    with pytest.raises(PermisoDenegado):
        s.enviar("A1", Rol.ALMACEN)


def test_revision_invalida():
    s = solicitud(nec())
    s.confirmar_necesidad("N1", "RF1", RF)
    with pytest.raises(InvalidTransition):
        s.rechazar_necesidad("N1", "RF1", RF)  # ya revisada
    with pytest.raises(ReglaDeNegocioViolada):
        s.confirmar_necesidad("NX", "RF1", RF)  # no existe
    s2 = solicitud(nec())
    with pytest.raises(ReglaDeNegocioViolada):
        s2.confirmar_necesidad("N1", "RF1", RF, cantidad=0)


def test_solicitud_enviada_es_inmutable():
    s = solicitud(nec())
    s.confirmar_necesidad("N1", "RF1", RF)
    s.enviar("RF1", RF)
    with pytest.raises(InvalidTransition):
        s.registrar_necesidad(nec("N2"))
    with pytest.raises(InvalidTransition):
        s.enviar("RF1", RF)
