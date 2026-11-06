"""US10 (sustituciones), US11/US12 (registros de venta especial) y US18 (reportes)."""
from datetime import date, datetime, timezone

import pytest

from src.application.reporte_service import Filtros
from src.application.venta_service import ItemVenta
from src.domain.errors import (
    InvalidTransition,
    NoEncontrado,
    PermisoDenegado,
    ReglaDeNegocioViolada,
)
from src.domain.solicitud_compra import MotivoNecesidad
from src.domain.value_objects import ResultadoRevision, Rol
from src.domain.venta import Receta

RF, CAJ, ALM, COMP = (Rol.RESPONSABLE_FARMACIA, Rol.CAJERO, Rol.ALMACEN, Rol.COMPRAS)


def receta():
    return Receta("R1", "Dr. Pérez", "CED-99", "Ana Gómez", date(2026, 11, 1))


# ------------------------------ US10: sustituciones ------------------------------
def _venta(ctx):
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P1", 2, "L1")], "V1")


def test_us10_autorizar_reemplaza_linea_y_registra(ctx):
    _venta(ctx)
    s = ctx.ventas.autorizar_sustitucion("V1", "P1", "P2", "sin existencia", "RF1", RF, "L2")
    assert s.estado.value == "AUTORIZADA" and s.alternativa == "P2"
    linea = ctx.store.ventas["V1"].lineas[0]
    assert (linea.producto_id, linea.cantidad, linea.lote_id) == ("P2", 2, "L2")
    assert ctx.store.sustituciones[s.id].motivo == "sin existencia"
    assert "SustitucionAutorizada" in [e.nombre for e in ctx.bus.publicados]
    assert "AUTORIZAR_SUSTITUCION" in [h.accion for h in ctx.store.historial]


def test_us10_solo_responsable_de_farmacia(ctx):
    _venta(ctx)
    with pytest.raises(PermisoDenegado):
        ctx.ventas.autorizar_sustitucion("V1", "P1", "P2", "m", "C1", CAJ)
    with pytest.raises(PermisoDenegado):
        ctx.ventas.rechazar_sustitucion("V1", "P1", "m", "C1", CAJ)


@pytest.mark.parametrize("producto,alt,motivo", [
    ("P1", "P2", "  "),          # sin motivo
    ("P1", "P1", "m"),           # misma alternativa
    ("P9", "P2", "m"),           # el producto no está en la venta
    ("P1", "P3", "m"),           # alternativa deshabilitada
])
def test_us10_reglas_y_rollback(ctx, producto, alt, motivo):
    _venta(ctx)
    with pytest.raises(ReglaDeNegocioViolada):
        ctx.ventas.autorizar_sustitucion("V1", producto, alt, motivo, "RF1", RF)
    assert len(ctx.store.sustituciones) == 0
    assert ctx.store.ventas["V1"].lineas[0].producto_id == "P1"


def test_us10_venta_completada_no_admite_sustitucion(ctx):
    _venta(ctx)
    ctx.ventas.completar_venta("V1", "C1")
    with pytest.raises(InvalidTransition):
        ctx.ventas.autorizar_sustitucion("V1", "P1", "P2", "m", "RF1", RF, "L2")
    assert len(ctx.store.sustituciones) == 0


def test_us10_rechazo_no_cambia_la_venta(ctx):
    _venta(ctx)
    s = ctx.ventas.rechazar_sustitucion("V1", "P1", "ninguna alternativa sirve", "RF1", RF)
    assert s.estado.value == "RECHAZADA" and s.alternativa is None
    assert ctx.store.ventas["V1"].lineas[0].producto_id == "P1"
    assert "SustitucionRechazada" in [e.nombre for e in ctx.bus.publicados]
    with pytest.raises(ReglaDeNegocioViolada):
        ctx.ventas.rechazar_sustitucion("V1", "P1", " ", "RF1", RF)


# ------------------------------ US11 / US12: ventas especiales ------------------------------
def _venta_con_receta(ctx):
    ctx.ventas.crear_venta("S1", "C1", [ItemVenta("P2", 1, "L2")], "VE")
    ctx.ventas.revisar_receta("VE", receta(), ResultadoRevision.ACEPTADA, "RF1", RF)
    _venta(ctx)       # V1 sin receta ni sustitución: no es venta especial


def test_us11_us12_responsable_ve_datos_personales(ctx):
    _venta_con_receta(ctx)
    regs = ctx.registros.listar(RF)
    assert [r.venta_id for r in regs] == ["VE"]
    r = regs[0]
    assert r.datos_personales_visibles and r.nombre_paciente == "Ana Gómez"
    assert (r.nombre_medico, r.cedula_medico) == ("Dr. Pérez", "CED-99")
    assert r.resultado_revision == "ACEPTADA" and r.revisada_por == "RF1"


def test_us12_cajero_no_ve_datos_personales(ctx):
    _venta_con_receta(ctx)
    r = ctx.registros.listar(CAJ)[0]
    assert not r.datos_personales_visibles
    assert (r.nombre_paciente, r.nombre_medico, r.cedula_medico) == (None, None, None)
    assert r.folio_receta == "R1"


@pytest.mark.parametrize("rol", [ALM, COMP])
def test_us12_otros_roles_denegados(ctx, rol):
    _venta_con_receta(ctx)
    with pytest.raises(PermisoDenegado):
        ctx.registros.listar(rol)
    with pytest.raises(PermisoDenegado):
        ctx.registros.obtener("VE", "X", rol)


def test_us12_obtener_audita_y_filtros(ctx):
    _venta_con_receta(ctx)
    assert ctx.registros.obtener("VE", "RF1", RF).venta_id == "VE"
    assert "CONSULTAR_REGISTRO_ESPECIAL" in [h.accion for h in ctx.store.historial]
    antes = len(ctx.store.historial)
    ctx.registros.obtener("VE", "C1", CAJ)
    assert len(ctx.store.historial) == antes           # la vista restringida no audita
    assert ctx.registros.listar(RF, sucursal_id="S9") == []
    assert ctx.registros.listar(RF, resultado="rechazada") == []
    assert len(ctx.registros.listar(RF, resultado="aceptada")) == 1
    with pytest.raises(NoEncontrado):
        ctx.registros.obtener("V1", "RF1", RF)          # venta sin registro especial
    with pytest.raises(NoEncontrado):
        ctx.registros.obtener("NOPE", "RF1", RF)


def test_us10_sustitucion_aparece_en_el_registro(ctx):
    _venta(ctx)
    ctx.ventas.autorizar_sustitucion("V1", "P1", "P2", "m", "RF1", RF, "L2")
    r = ctx.registros.listar(RF)[0]
    assert r.venta_id == "V1" and r.sustituciones[0].alternativa == "P2"


# ------------------------------ US18: reportes ------------------------------
def test_us18_caducidad_ordenada_y_filtrada(ctx):
    filas = ctx.reportes.generar("caducidad", RF, Filtros()).filas
    assert filas[0]["lote_id"] == "LC" and filas[0]["clasificacion"] == "CADUCADO"
    assert [f["dias_restantes"] for f in filas] == sorted(f["dias_restantes"] for f in filas)
    assert {f["lote_id"] for f in ctx.reportes.generar(
        "caducidad", ALM, Filtros(estado="caducado")).filas} == {"LC"}
    assert len(ctx.reportes.generar("caducidad", COMP, Filtros(sucursal_id="S2")).filas) == 1
    assert len(ctx.reportes.generar("caducidad", RF, Filtros(producto_id="P2")).filas) == 1
    assert len(ctx.reportes.generar("caducidad", RF, Filtros(lote_id="L1")).filas) == 2
    periodo = Filtros(desde=date(2027, 1, 1), hasta=date(2027, 12, 31))
    assert {f["lote_id"] for f in ctx.reportes.generar("caducidad", RF, periodo).filas} == {
        "L1", "L2"}


def test_us18_retiros_diferencias_ajustes_solicitudes(ctx):
    ctx.inventario.registrar_retiro("L1", "alerta", "RF1", RF, "R1")
    ctx.inventario.registrar_ejecucion_retiro("R1", "S1", 5, 5, "A1")
    r = ctx.reportes.generar("retiros", RF, Filtros(sucursal_id="S1", lote_id="L1")).filas
    assert len(r) == 1 and r[0]["retiradas"] == 5 and r[0]["sucursales"] == ["S1"]
    assert ctx.reportes.generar("retiros", RF, Filtros(sucursal_id="S2")).total == 0
    assert ctx.reportes.generar("retiros", RF, Filtros(estado="en_ejecucion")).total == 1

    ctx.inventario.registrar_diferencia("S1", "P1", "L1", 7, "A1", diferencia_id="D1")
    ctx.inventario.investigar_diferencia("D1", "RF1", "error de captura", "conteo ciego")
    ctx.inventario.solicitar_ajuste("D1", "A1", "corrección", "J1")
    d = ctx.reportes.generar("diferencias", ALM, Filtros(producto_id="P1")).filas
    assert d[0]["delta"] == -3 and d[0]["sucursal_id"] == "S1"
    assert ctx.reportes.generar("diferencias", ALM, Filtros(sucursal_id="S2")).total == 0
    a = ctx.reportes.generar("ajustes", RF, Filtros(sucursal_id="S1")).filas
    assert a[0]["cantidad_anterior"] == 10 and a[0]["cantidad_nueva"] == 7
    assert ctx.reportes.generar("ajustes", RF, Filtros(producto_id="P2")).total == 0
    hoy = datetime.now(timezone.utc).date()    # las entidades fechan con reloj real (UTC)
    assert ctx.reportes.generar("ajustes", RF, Filtros(desde=hoy, hasta=hoy)).total == 1
    assert ctx.reportes.generar("ajustes", RF, Filtros(desde=date(2030, 1, 1))).total == 0

    ctx.reposicion.crear_solicitud("S1", "A1", "SC1")
    ctx.reposicion.registrar_necesidad("SC1", "P1", 20, MotivoNecesidad.FALTANTE, "A1", "N1")
    s = ctx.reportes.generar("solicitudes", COMP, Filtros(producto_id="P1")).filas
    assert s[0]["estado"] == "EN_REVISION" and s[0]["necesidades"] == 1
    assert s[0]["horas_hasta_envio"] is None
    assert ctx.reportes.generar("solicitudes", COMP, Filtros(producto_id="P2")).total == 0
    ctx.reposicion.confirmar_necesidad("SC1", "N1", "RF1", RF)
    ctx.reposicion.enviar_solicitud("SC1", "RF1", RF)
    s = ctx.reportes.generar("solicitudes", COMP, Filtros(estado="enviada")).filas
    assert s[0]["confirmadas"] == 1 and s[0]["horas_hasta_envio"] is not None


def test_us18_permisos_y_tipo_invalido(ctx):
    with pytest.raises(PermisoDenegado):
        ctx.reportes.generar("caducidad", CAJ, Filtros())
    with pytest.raises(ReglaDeNegocioViolada):
        ctx.reportes.generar("inexistente", RF, Filtros())
