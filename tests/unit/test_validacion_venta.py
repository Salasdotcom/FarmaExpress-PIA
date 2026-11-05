"""Cubre DS-01 y DS-02 y la composición AND/OR/NOT de Specifications."""
from datetime import date
from decimal import Decimal

from src.domain.existencia import Existencia
from src.domain.lote import Lote
from src.domain.services import ServicioDeValidacionDeVenta
from src.domain.specifications import (
    ContextoDeValidacion,
    RecetaAceptada,
    SinLoteRetirado,
    SinMedicamentoCaducado,
    SinRecetaRequerida,
)
from src.domain.value_objects import Dinero, ResultadoRevision
from src.domain.venta import LineaDeVenta, Receta, Venta

HOY = date(2026, 11, 5)


def ctx(caduca=date(2027, 6, 1), retirado=False, stock=10, cant=2, receta=False,
        resultado=None, sucursal="S1"):
    v = Venta("V1", "S1", "C1")
    v.agregar_linea(LineaDeVenta("P1", cant, Dinero(Decimal("10")), "L1", receta))
    if receta and resultado:
        v.registrar_revision_receta(
            Receta("R", "Dr", "1", "Pac", HOY), resultado, "RF1")
    lote = Lote("L1", "P1", caduca, retirado)
    ex = Existencia("P1", sucursal, stock, "L1")
    return ContextoDeValidacion(v, HOY, {"L1": lote}, {ex.clave: ex})


svc = ServicioDeValidacionDeVenta()


def test_venta_valida():
    r = svc.validar(ctx())
    assert r.valida and r.violaciones == ()
    assert svc.especificacion_completa().is_satisfied_by(ctx())


def test_ds02_caducado_hoy_bloquea():
    r = svc.validar(ctx(caduca=HOY))
    assert not r.valida and "MEDICAMENTO_CADUCADO" in r.violaciones


def test_vence_manana_no_bloquea():
    assert svc.validar(ctx(caduca=date(2026, 11, 6))).valida


def test_lote_retirado_bloquea():
    assert "LOTE_RETIRADO" in svc.validar(ctx(retirado=True)).violaciones


def test_existencia_insuficiente_y_limite():
    assert "EXISTENCIA_INSUFICIENTE" in svc.validar(ctx(stock=1, cant=2)).violaciones
    assert svc.validar(ctx(stock=2, cant=2)).valida


def test_existencia_en_otra_sucursal_no_cuenta():
    assert "EXISTENCIA_INSUFICIENTE" in svc.validar(ctx(sucursal="S2")).violaciones


def test_receta_sin_revision_bloquea():
    assert "RECETA_NO_ACEPTADA" in svc.validar(ctx(receta=True)).violaciones


def test_receta_no_aceptada_bloquea_y_aceptada_pasa():
    for malo in (ResultadoRevision.INCOMPLETA, ResultadoRevision.VENCIDA,
                 ResultadoRevision.NO_ACEPTADA):
        assert not svc.validar(ctx(receta=True, resultado=malo)).valida
    assert svc.validar(ctx(receta=True, resultado=ResultadoRevision.ACEPTADA)).valida


def test_acumula_varias_violaciones():
    r = svc.validar(ctx(caduca=HOY, retirado=True, stock=0))
    assert set(r.violaciones) == {
        "MEDICAMENTO_CADUCADO", "LOTE_RETIRADO", "EXISTENCIA_INSUFICIENTE"}


def test_venta_ya_completada_no_valida():
    c = ctx()
    c.venta.completar()
    assert "VENTA_NO_EN_PROCESO" in svc.validar(c).violaciones


def test_lote_desconocido_se_trata_como_no_vendible():
    c = ctx()
    assert not SinMedicamentoCaducado().is_satisfied_by(
        ContextoDeValidacion(c.venta, HOY, {}, c.existencias))


def test_composicion_and_or_not():
    c = ctx(caduca=HOY)  # caducado, sin receta
    assert (~SinMedicamentoCaducado()).is_satisfied_by(c)
    assert not (SinMedicamentoCaducado() & SinLoteRetirado()).is_satisfied_by(c)
    assert (SinMedicamentoCaducado() | SinLoteRetirado()).is_satisfied_by(c)
    assert (SinRecetaRequerida() | RecetaAceptada()).is_satisfied_by(c)
