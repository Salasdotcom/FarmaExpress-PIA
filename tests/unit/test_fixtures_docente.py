"""Fase 4: paquete de pruebas del profesor (120 casos + 20 transiciones) ejecutado contra el
dominio y el servicio reales. El oráculo oficial lo reserva el docente; aquí el oráculo es una
expresión booleana independiente calculada directo de las columnas del CSV."""
import csv
from decimal import Decimal
from pathlib import Path

import pytest

from src.domain.elegibilidad import (
    ActorActivo,
    OperacionAutorizada,
    OperacionConLineas,
    OperacionEvaluable,
    PromocionActiva,
    TotalMinimo,
    beneficio_referencia,
    puede_procesarse,
)
from src.domain.value_objects import Dinero
from src.infrastructure.fixtures_csv import (
    cargar_paquete,
    crear_entorno,
    ejecutar_caso,
    ejecutar_transicion,
    evaluable,
    total_de,
)

CARPETA = Path(__file__).resolve().parent.parent / "fixtures" / "docente"
PAQUETE = cargar_paquete(CARPETA)


def _op(**kw) -> OperacionEvaluable:
    base = dict(operacion_id="X", actor_id="A", actor_activo=True, actor_preferente=True,
                numero_de_lineas=1, total=Dinero(Decimal("1500")), promocion_activa=False,
                autorizada=True)
    return OperacionEvaluable(**{**base, **kw})


# ------------------------------ carga del paquete ------------------------------
def test_paquete_tiene_los_volumenes_esperados():
    p = PAQUETE
    assert (len(p.actores), len(p.catalogo), len(p.operaciones)) == (40, 20, 60)
    assert sum(len(v) for v in p.detalle.values()) == 117
    assert (len(p.casos), len(p.transiciones)) == (120, 20)
    assert all(o["estado_inicial"] == "CREADO" for o in p.operaciones)


def test_total_exacto_con_decimal():
    # FAR-O001 = 3 x 1019.00 + 4 x 1374.00
    assert total_de(PAQUETE, "FAR-O001").monto == Decimal("8553.00")
    assert total_de(PAQUETE, "FAR-O013").monto == Decimal("0")     # operación sin detalle


# ------------------------------ Specifications ------------------------------
def test_specifications_atomicas():
    assert ActorActivo().is_satisfied_by(_op()) and not ActorActivo().is_satisfied_by(
        _op(actor_activo=False))
    assert not OperacionConLineas().is_satisfied_by(_op(numero_de_lineas=0))
    assert not OperacionAutorizada().is_satisfied_by(_op(autorizada=False))
    assert PromocionActiva().is_satisfied_by(_op(promocion_activa=True))


def test_total_minimo_es_inclusivo_en_1500():
    assert TotalMinimo().is_satisfied_by(_op(total=Dinero(Decimal("1500.00"))))
    assert not TotalMinimo().is_satisfied_by(_op(total=Dinero(Decimal("1499.99"))))


def test_composicion_and_or_not():
    assert puede_procesarse.is_satisfied_by(_op())
    assert not puede_procesarse.is_satisfied_by(_op(actor_activo=False))
    assert beneficio_referencia.is_satisfied_by(_op())
    assert not beneficio_referencia.is_satisfied_by(_op(promocion_activa=True))      # NOT
    assert not beneficio_referencia.is_satisfied_by(_op(actor_preferente=False))
    o = ActorActivo() | OperacionAutorizada()                                        # OR
    assert o.is_satisfied_by(_op(actor_activo=False)) and not o.is_satisfied_by(
        _op(actor_activo=False, autorizada=False))


# ------------------------------ 120 casos de prueba ------------------------------
@pytest.mark.parametrize("caso", PAQUETE.casos, ids=lambda c: c["caso_id"])
def test_casos_contra_oraculo_independiente(caso):
    res = ejecutar_caso(PAQUETE, caso)
    op = next(o for o in PAQUETE.operaciones if o["operacion_id"] == caso["operacion_id"])
    actor = PAQUETE.actores[op["actor_id"]]
    lineas = PAQUETE.detalle.get(op["operacion_id"], [])
    total = sum(Decimal(PAQUETE.catalogo[x["recurso_id"]]["precio_mxn"]) * int(x["cantidad"])
                for x in lineas)
    if caso["tipo_prueba"] == "validar_operacion":
        esperado = actor["activo"] == "1" and len(lineas) > 0 and op["autorizado"] == "1"
    else:
        esperado = (actor["es_preferente"] == "1" and total >= 1500
                    and op["promocion_activa"] == "0")
    assert (res["cumple"] == "1") is esperado
    assert res["resultado_alumno"] != "PENDIENTE" and res["total_mxn"] == f"{total:.2f}"


def test_resultados_conocidos():
    r = {c["caso_id"]: ejecutar_caso(PAQUETE, c) for c in PAQUETE.casos}
    assert r["FAR-T001"]["resultado_alumno"] == "VALIDA"
    assert r["FAR-B001"]["resultado_alumno"] == "SIN BENEFICIO: NO_PREFERENTE"
    assert r["FAR-B002"]["resultado_alumno"] == "CON BENEFICIO"        # C025 preferente, 7559
    assert "SIN_LINEAS" in r["FAR-T013"]["resultado_alumno"]            # FAR-O013 sin detalle
    assert "SIN_AUTORIZACION" in r["FAR-T008"]["resultado_alumno"]
    assert "ACTOR_INACTIVO" in r["FAR-T028"]["resultado_alumno"]        # FAR-C007 inactivo
    assert any("PROMOCION_ACTIVA" in x["resultado_alumno"] for x in r.values())
    assert evaluable(PAQUETE, "FAR-O002").actor_preferente is True


# ------------------------------ 20 transiciones ------------------------------
@pytest.fixture(scope="module")
def transiciones():
    return {t["caso_id"]: ejecutar_transicion(PAQUETE, t) for t in PAQUETE.transiciones}


def test_ninguna_transicion_queda_pendiente_ni_sin_traza(transiciones):
    assert len(transiciones) == 20
    for t in transiciones.values():
        assert t["resultado_alumno"] == "OK" or t["resultado_alumno"].startswith("EXCEPCION")
        assert t["estado_final"] in {"CREADO", "EN_PROCESO", "COMPLETADA", "CANCELADA"}
        if t["resultado_alumno"] == "OK":
            assert t["evento"]       # toda transición exitosa publica un Domain Event


def test_completar_cancelar_y_eventos(transiciones):
    assert transiciones["FAR-S001"]["estado_final"] == "COMPLETADA"
    assert transiciones["FAR-S001"]["evento"] == "VentaCompletada"
    assert transiciones["FAR-S002"]["estado_final"] == "CANCELADA"
    assert transiciones["FAR-S002"]["evento"] == "VentaCancelada"


def test_repetir_aprobacion_y_saltar_estado_son_invalidas(transiciones):
    for caso in ("FAR-S003", "FAR-S004", "FAR-S009", "FAR-S018"):
        assert "InvalidTransition" in transiciones[caso]["resultado_alumno"]


def test_precondiciones_del_modelo_bloquean(transiciones):
    assert "SIN_AUTORIZACION" in transiciones["FAR-S008"]["resultado_alumno"]
    assert "SIN_LINEAS" in transiciones["FAR-S013"]["resultado_alumno"]
    assert "no está habilitado" in transiciones["FAR-S005"]["resultado_alumno"]   # FAR-P011


def test_completar_descuenta_inventario_y_cancelar_no():
    ent = crear_entorno(PAQUETE)
    ant = ent.store.existencias[("FAR-P009", "LOT-FAR-P009", "SUC-01")].cantidad
    ejecutar_transicion(PAQUETE, PAQUETE.transiciones[0], ent)            # FAR-O001 completar
    assert ent.store.existencias[("FAR-P009", "LOT-FAR-P009", "SUC-01")].cantidad == ant - 3
    ent2 = crear_entorno(PAQUETE)
    ejecutar_transicion(PAQUETE, PAQUETE.transiciones[1], ent2)           # FAR-O002 cancelar
    assert ent2.store.existencias[("FAR-P012", "LOT-FAR-P012", "SUC-01")].cantidad == 46


# ------------------------------ evidencia generada ------------------------------
def test_script_genera_evidencia_sin_pendientes(tmp_path):
    import importlib.util
    ruta = Path(__file__).resolve().parent.parent.parent / "scripts" / "ejecutar_fixtures.py"
    spec = importlib.util.spec_from_file_location("ejecutar_fixtures", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    casos, trans = mod.main(CARPETA, tmp_path)
    assert (len(casos), len(trans)) == (120, 20)
    with open(tmp_path / "casos_prueba_resultados.csv", "rb") as f:
        assert f.read(3) == b"\xef\xbb\xbf"                                   # UTF-8 con BOM
    with open(tmp_path / "casos_prueba_resultados.csv", encoding="utf-8-sig") as f:
        assert all(r["resultado_alumno"] != "PENDIENTE" for r in csv.DictReader(f))
