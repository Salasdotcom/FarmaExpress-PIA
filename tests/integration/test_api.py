"""Pruebas de la API REST (contrato HTTP: 200/201, 400, 401, 403, 404, 409, 422)."""
import pytest
from fastapi.testclient import TestClient

from src.api.container import build_container
from src.api.main import create_app
from src.infrastructure.seed import cargar_demo
from tests.conftest import FakeClock

CAJERO = {"X-User-Id": "C1", "X-User-Role": "CAJERO"}
RF = {"X-User-Id": "RF1", "X-User-Role": "RESPONSABLE_FARMACIA"}
RF2 = {"X-User-Id": "RF2", "X-User-Role": "RESPONSABLE_FARMACIA"}
ALM = {"X-User-Id": "A1", "X-User-Role": "ALMACEN"}
COMPRAS = {"X-User-Id": "K1", "X-User-Role": "COMPRAS"}


@pytest.fixture
def client():
    container = build_container("sqlite+pysqlite:///:memory:", clock=FakeClock())
    with TestClient(create_app(container, seed=True)) as c:
        yield c
    container.engine.dispose()


def venta(client, items, sucursal="SUC-01", headers=CAJERO):
    datos = {"sucursal_id": sucursal}
    if items:
        datos.update(items[0])
    r = client.post("/ventas", data=datos, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def stock(client, producto, sucursal, lote):
    r = client.get(f"/existencias/{producto}", headers=CAJERO)
    return next(e["cantidad"] for e in r.json()["existencias"]
                if e["sucursal_id"] == sucursal and e["lote_id"] == lote)


# ---------------------------- infraestructura ----------------------------
def test_health_openapi_y_swagger(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert "/ventas/{venta_id}/completar" in paths and "/auditoria" in paths


def test_seed_es_idempotente():
    c = build_container("sqlite+pysqlite:///:memory:", clock=FakeClock())
    from src.infrastructure.db import init_db
    init_db(c.engine)
    assert cargar_demo(c.uow_factory, c.clock) is True
    assert cargar_demo(c.uow_factory, c.clock) is False
    c.engine.dispose()


# ------------------------------ identidad (401) ------------------------------
def test_sin_encabezados_o_rol_invalido_401(client):
    assert client.get("/existencias/MED-001").status_code == 401
    r = client.get("/existencias/MED-001", headers={"X-User-Id": "x", "X-User-Role": "ROOT"})
    assert r.status_code == 401


# ------------------------------ ventas: flujo feliz ------------------------------
def test_ds01_completar_venta(client):
    vid = venta(client, [{"producto_id": "MED-001", "cantidad": 3, "lote_id": "LOT-001"}])
    r = client.post(f"/ventas/{vid}/completar", headers=CAJERO)
    assert r.status_code == 200
    body = r.json()
    assert body["estado"] == "COMPLETADA" and body["total"] == "106.50"
    assert "completada" in body["mensaje"] and "106.50" in body["mensaje"]
    assert stock(client, "MED-001", "SUC-01", "LOT-001") == 47


def test_agregar_linea_y_consultar(client):
    vid = venta(client, [{"producto_id": "MED-001", "cantidad": 1, "lote_id": "LOT-001"}])
    r = client.post(f"/ventas/{vid}/lineas", headers=CAJERO,
                    data={"producto_id": "MED-002", "cantidad": 2})
    assert r.status_code == 200 and len(r.json()["lineas"]) == 2
    assert client.get(f"/ventas/{vid}", headers=CAJERO).json()["total"] == "139.50"


# ------------------------------ ventas: bloqueos (422) ------------------------------
def test_ds02_medicamento_caducado_422_y_sin_cambios(client):
    vid = venta(client, [{"producto_id": "MED-002", "cantidad": 1, "lote_id": "LOT-004"}])
    r = client.post(f"/ventas/{vid}/completar", headers=CAJERO)
    assert r.status_code == 422
    assert r.json()["codigo"] == "VENTA_NO_COMPLETABLE"
    assert "MEDICAMENTO_CADUCADO" in r.json()["violaciones"]
    assert any("caducado" in t for t in r.json()["explicacion"])
    assert client.get(f"/ventas/{vid}", headers=CAJERO).json()["estado"] == "EN_PROCESO"
    assert stock(client, "MED-002", "SUC-01", "LOT-004") == 12


def test_lote_retirado_se_bloquea_en_otra_sucursal(client):
    assert client.post("/lotes/LOT-001/retiro", headers=RF,
                       data={"motivo": "alerta sanitaria"}).status_code == 201
    vid = venta(client, [{"producto_id": "MED-001", "cantidad": 1, "lote_id": "LOT-001"}],
                sucursal="SUC-02")
    r = client.post(f"/ventas/{vid}/completar", headers=CAJERO)
    assert r.status_code == 422 and "LOTE_RETIRADO" in r.json()["violaciones"]


def test_existencia_insuficiente_422(client):
    vid = venta(client, [{"producto_id": "MED-001", "cantidad": 21, "lote_id": "LOT-001"}],
                sucursal="SUC-02")  # SUC-02 tiene 20
    r = client.post(f"/ventas/{vid}/completar", headers=CAJERO)
    assert r.status_code == 422 and "EXISTENCIA_INSUFICIENTE" in r.json()["violaciones"]


def test_venta_con_receta_flujo_completo(client):
    vid = venta(client, [{"producto_id": "MED-003", "cantidad": 1, "lote_id": "LOT-005"}])
    assert client.post(f"/ventas/{vid}/completar", headers=CAJERO).status_code == 422
    receta = {"folio": "R-1", "medico": "Dr. Pérez", "cedula_medico": "12345",
              "nombre_paciente": "Ana", "fecha_emision": "2026-11-01"}
    r = client.post(f"/ventas/{vid}/receta/revision", headers=RF,
                    data={**receta, "resultado": "INCOMPLETA"})
    assert r.status_code == 200
    assert client.post(f"/ventas/{vid}/completar", headers=CAJERO).status_code == 422
    client.post(f"/ventas/{vid}/receta/revision", headers=RF,
                data={**receta, "resultado": "ACEPTADA"})
    assert client.post(f"/ventas/{vid}/completar", headers=CAJERO).json()["estado"] == "COMPLETADA"


def test_cantidad_cero_es_regla_de_negocio_422(client):
    r = client.post("/ventas", headers=CAJERO, data={
        "sucursal_id": "SUC-01", "producto_id": "MED-001", "cantidad": 0})
    assert r.status_code == 422 and r.json()["codigo"] == "REGLA_DE_NEGOCIO"


def test_producto_deshabilitado_422(client):
    r = client.post("/ventas", headers=CAJERO, data={
        "sucursal_id": "SUC-01", "producto_id": "MED-005", "cantidad": 1})
    assert r.status_code == 422


# ------------------------------ 400 / 403 / 404 / 409 ------------------------------
def test_solicitud_mal_formada_400(client):
    r = client.post("/ventas", headers=CAJERO, data={"producto_id": "MED-001"})  # falta sucursal_id
    assert r.status_code == 400 and r.json()["codigo"] == "SOLICITUD_INVALIDA"
    r = client.post("/ventas", headers=CAJERO, data={
        "sucursal_id": "S", "producto_id": "MED-001", "cantidad": "muchas"})
    assert r.status_code == 400 and r.json()["errores"]


def test_404_recursos_inexistentes(client):
    assert client.get("/ventas/NOPE", headers=CAJERO).status_code == 404
    assert client.get("/lotes/NOPE/caducidad", headers=CAJERO).status_code == 404
    assert client.get("/existencias/NOPE", headers=CAJERO).status_code == 404
    r = client.post("/ventas", headers=CAJERO, data={
        "sucursal_id": "S", "producto_id": "NOPE", "cantidad": 1})
    assert r.status_code == 404 and r.json()["codigo"] == "NO_ENCONTRADO"


def test_409_completar_venta_cancelada_o_completada(client):
    vid = venta(client, [{"producto_id": "MED-001", "cantidad": 1, "lote_id": "LOT-001"}])
    assert client.post(f"/ventas/{vid}/cancelar", headers=CAJERO,
                       data={"motivo": "cliente se fue"}).json()["estado"] == "CANCELADA"
    r = client.post(f"/ventas/{vid}/completar", headers=CAJERO)
    assert r.status_code == 409 and r.json()["codigo"] == "TRANSICION_INVALIDA"
    vid2 = venta(client, [{"producto_id": "MED-001", "cantidad": 1, "lote_id": "LOT-001"}])
    client.post(f"/ventas/{vid2}/completar", headers=CAJERO)
    assert client.post(f"/ventas/{vid2}/completar", headers=CAJERO).status_code == 409
    assert client.post(f"/ventas/{vid2}/lineas", headers=CAJERO,
                       data={"producto_id": "MED-001", "cantidad": 1}).status_code == 409
    assert stock(client, "MED-001", "SUC-01", "LOT-001") == 49  # sin doble descuento


def test_cancelar_sin_cuerpo(client):
    vid = venta(client, [{"producto_id": "MED-001", "cantidad": 1, "lote_id": "LOT-001"}])
    assert client.post(f"/ventas/{vid}/cancelar", headers=CAJERO).status_code == 200


def test_403_permisos_por_rol(client):
    vid = venta(client, [{"producto_id": "MED-003", "cantidad": 1, "lote_id": "LOT-005"}])
    receta = {"folio": "R", "medico": "M", "cedula_medico": "1", "nombre_paciente": "P",
              "fecha_emision": "2026-11-01", "resultado": "ACEPTADA"}
    assert client.post(f"/ventas/{vid}/receta/revision", headers=CAJERO,
                       data=receta).status_code == 403          # cajero no revisa recetas
    assert client.post("/lotes/LOT-001/retiro", headers=CAJERO,
                       data={"motivo": "x"}).status_code == 403  # sólo el responsable retira
    assert client.post("/lotes/LOT-001/retiro", headers=ALM,
                       data={"motivo": "x"}).status_code == 403
    assert client.get("/auditoria", headers=CAJERO).status_code == 403
    assert client.post("/ventas", headers=ALM, data={"sucursal_id": "S"}).status_code == 403


# ------------------------------ caducidad (US01) ------------------------------
@pytest.mark.parametrize("lote,clase,dias,vendible", [
    ("LOT-001", "NORMAL", 400, True), ("LOT-002", "PROXIMO_A_CADUCAR", 45, True),
    ("LOT-003", "CRITICO", 7, True), ("LOT-004", "CADUCADO", 0, False)])
def test_caducidad_por_lote(client, lote, clase, dias, vendible):
    r = client.get(f"/lotes/{lote}/caducidad", headers=CAJERO).json()
    assert (r["clasificacion"], r["dias_restantes"], r["vendible"]) == (clase, dias, vendible)


def test_existencias_entre_sucursales_son_informativas(client):
    r = client.get("/existencias/MED-001", headers=CAJERO).json()
    assert r["informativo"] is True
    assert {e["sucursal_id"] for e in r["existencias"]} == {"SUC-01", "SUC-02"}
    assert stock(client, "MED-001", "SUC-02", "LOT-001") == 20


# ------------------------------ retiro de lote (US03/US04) ------------------------------
def test_retiro_completo(client):
    r = client.post("/lotes/LOT-002/retiro", headers=RF, data={"motivo": "retiro del fabricante"})
    assert r.status_code == 201
    rid = r.json()["id"]
    assert client.get("/lotes/LOT-002/caducidad", headers=CAJERO).json()["vendible"] is False
    ej = client.post(f"/retiros/{rid}/ejecuciones", headers=ALM,
                     data={"sucursal_id": "SUC-01", "identificadas": 30, "retiradas": 30})
    assert ej.status_code == 201 and ej.json()["estado"] == "EN_EJECUCION"
    assert client.post(f"/retiros/{rid}/concluir", headers=ALM).json()["estado"] == "EJECUTADO"
    assert client.post(f"/retiros/{rid}/concluir", headers=ALM).status_code == 409
    assert client.post(f"/retiros/{rid}/ejecuciones", headers=ALM, data={
        "sucursal_id": "SUC-01", "identificadas": 1, "retiradas": 5}).status_code == 409
    assert client.get(f"/retiros/{rid}", headers=ALM).json()["total_retiradas"] == 30


def test_retiro_retiradas_mayor_que_identificadas_422(client):
    rid = client.post("/lotes/LOT-002/retiro", headers=RF, data={"motivo": "m"}).json()["id"]
    r = client.post(f"/retiros/{rid}/ejecuciones", headers=ALM,
                    data={"sucursal_id": "SUC-01", "identificadas": 5, "retiradas": 6})
    assert r.status_code == 422


# ------------------------------ diferencia -> ajuste (US15-US17) ------------------------------
def diferencia_investigada(client):
    d = client.post("/diferencias", headers=ALM, data={
        "sucursal_id": "SUC-01", "producto_id": "MED-001", "lote_id": "LOT-001",
        "cantidad_fisica": 47}).json()
    assert d["delta"] == -3 and d["cantidad_registrada"] == 50
    r = client.post(f"/diferencias/{d['id']}/investigacion", headers=ALM,
                    data={"causa": "error de captura", "evidencia": "conteo ciego"})
    assert r.json()["ajustable"] is True
    return d["id"]


def test_ajuste_flujo_completo_con_separacion_de_funciones(client):
    did = diferencia_investigada(client)
    aj = client.post("/ajustes", headers=ALM, data={"diferencia_id": did, "motivo": "corrección"})
    assert aj.status_code == 201
    aid = aj.json()["id"]
    assert stock(client, "MED-001", "SUC-01", "LOT-001") == 50  # aún sin cambio
    # Almacén intenta autorizar su propio ajuste -> 403
    r = client.post(f"/ajustes/{aid}/autorizar", headers=ALM)
    assert r.status_code == 403 and r.json()["codigo"] == "PERMISO_DENEGADO"
    # aplicar sin autorización -> 409 y la existencia no cambia
    assert client.post(f"/ajustes/{aid}/aplicar", headers=ALM).status_code == 409
    assert stock(client, "MED-001", "SUC-01", "LOT-001") == 50
    # el responsable autoriza y Almacén aplica
    assert client.post(f"/ajustes/{aid}/autorizar", headers=RF).json()["estado"] == "AUTORIZADO"
    assert client.post(f"/ajustes/{aid}/aplicar", headers=ALM).json()["estado"] == "APLICADO"
    assert stock(client, "MED-001", "SUC-01", "LOT-001") == 47
    assert client.get(f"/ajustes/{aid}", headers=ALM).json()["autorizador_id"] == "RF1"


def test_responsable_que_ejecuta_no_autoriza_su_propio_ajuste(client):
    did = diferencia_investigada(client)
    aid = client.post("/ajustes", headers=RF, data={
        "diferencia_id": did, "motivo": "m"}).json()["id"]
    assert client.post(f"/ajustes/{aid}/autorizar", headers=RF).status_code == 403
    assert client.post(f"/ajustes/{aid}/autorizar", headers=RF2).status_code == 200


def test_ajuste_rechazado_y_diferencia_sin_investigar(client):
    d = client.post("/diferencias", headers=ALM, data={
        "sucursal_id": "SUC-01", "producto_id": "MED-001", "lote_id": "LOT-001",
        "cantidad_fisica": 40}).json()
    r = client.post("/ajustes", headers=ALM, data={"diferencia_id": d["id"], "motivo": "m"})
    assert r.status_code == 422  # RN-09: requiere causa y evidencia
    client.post(f"/diferencias/{d['id']}/investigacion", headers=ALM,
                data={"causa": "merma", "evidencia": "acta"})
    aid = client.post("/ajustes", headers=ALM, data={
        "diferencia_id": d["id"], "motivo": "m"}).json()["id"]
    assert client.post(f"/ajustes/{aid}/rechazar", headers=RF).json()["estado"] == "RECHAZADO"
    assert client.post(f"/ajustes/{aid}/aplicar", headers=ALM).status_code == 409


def test_diferencia_igual_o_sin_existencia(client):
    base = {"sucursal_id": "SUC-01", "producto_id": "MED-001", "lote_id": "LOT-001"}
    assert client.post("/diferencias", headers=ALM,
                       data={**base, "cantidad_fisica": 50}).status_code == 422
    assert client.post("/diferencias", headers=ALM,
                       data={**base, "sucursal_id": "SUC-99", "cantidad_fisica": 1}
                       ).status_code == 404
    assert client.get("/diferencias/NOPE", headers=ALM).status_code == 404


# ------------------------------ reposición (US06-US08) ------------------------------
def test_reposicion_flujo_completo(client):
    sid = client.post("/solicitudes-compra", headers=ALM,
                      data={"sucursal_id": "SUC-01"}).json()["id"]
    n1 = client.post(f"/solicitudes-compra/{sid}/necesidades", headers=ALM, data={
        "producto_id": "MED-001", "cantidad": 40, "motivo": "FALTANTE"})
    assert n1.status_code == 201
    client.post(f"/solicitudes-compra/{sid}/necesidades", headers=ALM, data={
        "producto_id": "MED-002", "cantidad": 10, "motivo": "EXISTENCIA_BAJA"})
    necs = client.get(f"/solicitudes-compra/{sid}", headers=COMPRAS).json()["necesidades"]
    assert [n["estado"] for n in necs] == ["PENDIENTE_REVISION"] * 2
    # Almacén no confirma; el responsable sí
    base = f"/solicitudes-compra/{sid}/necesidades"
    assert client.post(f"{base}/{necs[0]['id']}/confirmar", headers=ALM).status_code == 403
    assert client.post(f"{base}/{necs[0]['id']}/confirmar", headers=RF,
                       data={"cantidad": 35}).status_code == 200
    assert client.post(f"{base}/{necs[1]['id']}/rechazar", headers=RF).status_code == 200
    r = client.post(f"/solicitudes-compra/{sid}/enviar", headers=RF)
    assert r.status_code == 200 and r.json()["estado"] == "ENVIADA"
    assert r.json()["lineas_a_comprar"] == [{"producto_id": "MED-001", "cantidad": 35}]
    assert client.post(f"/solicitudes-compra/{sid}/enviar", headers=RF).status_code == 409


def test_reposicion_errores(client):
    sid = client.post("/solicitudes-compra", headers=ALM,
                      data={"sucursal_id": "SUC-01"}).json()["id"]
    assert client.post(f"/solicitudes-compra/{sid}/necesidades", headers=ALM, data={
        "producto_id": "MED-001", "cantidad": 1, "motivo": "ANTOJO"}).status_code == 400
    assert client.post(f"/solicitudes-compra/{sid}/enviar", headers=RF).status_code == 422
    assert client.get("/solicitudes-compra/NOPE", headers=COMPRAS).status_code == 404
    assert client.get(f"/solicitudes-compra/{sid}", headers=CAJERO).status_code == 403


# ------------------------------ auditoría (RF-16) ------------------------------
def test_auditoria_registra_y_filtra(client):
    vid = venta(client, [{"producto_id": "MED-001", "cantidad": 1, "lote_id": "LOT-001"}])
    client.post(f"/ventas/{vid}/completar", headers=CAJERO)
    r = client.get("/auditoria", headers=RF, params={"entidad_id": vid})
    assert r.status_code == 200
    assert [a["accion"] for a in r.json()] == ["CREAR_VENTA", "COMPLETAR_VENTA"]
    assert r.json()[1]["usuario"] == "C1" and r.json()[1]["despues"] == "COMPLETADA"
    solo = client.get("/auditoria", headers=RF, params={"accion": "completar_venta"}).json()
    assert len(solo) == 1


# ------------------------------ US10 / US11 / US12 / US18 ------------------------------
def test_us10_sustitucion_api(client):
    vid = venta(client, [{"producto_id": "MED-001", "cantidad": 2, "lote_id": "LOT-001"}])
    datos = {"producto_solicitado": "MED-001", "alternativa_id": "MED-003",
             "motivo": "sin existencia", "lote_id": "LOT-005"}
    assert client.post(f"/ventas/{vid}/sustituciones", headers=CAJERO,
                       data=datos).status_code == 403
    r = client.post(f"/ventas/{vid}/sustituciones", headers=RF, data=datos)
    assert r.status_code == 201 and r.json()["estado"] == "AUTORIZADA"
    assert "MED-003" in r.json()["mensaje"]
    linea = client.get(f"/ventas/{vid}", headers=CAJERO).json()["lineas"][0]
    assert linea["producto_id"] == "MED-003" and linea["cantidad"] == 2
    r = client.post(f"/ventas/{vid}/sustituciones/rechazo", headers=RF,
                    data={"producto_solicitado": "MED-003", "motivo": "sin alternativas"})
    assert r.status_code == 201 and r.json()["estado"] == "RECHAZADA"
    r = client.post("/ventas/NOPE/sustituciones", headers=RF, data=datos)
    assert r.status_code == 404
    r = client.post(f"/ventas/{vid}/sustituciones", headers=RF,
                    data={**datos, "motivo": " ", "producto_solicitado": "MED-003",
                          "alternativa_id": "MED-001"})
    assert r.status_code == 422


def test_us11_us12_registros_con_permisos(client):
    vid = venta(client, [{"producto_id": "MED-003", "cantidad": 1, "lote_id": "LOT-005"}])
    client.post(f"/ventas/{vid}/receta/revision", headers=RF, data={
        "folio": "R-1", "medico": "Dr. Pérez", "cedula_medico": "12345",
        "nombre_paciente": "Ana", "fecha_emision": "2026-11-01", "resultado": "ACEPTADA"})
    completo = client.get(f"/registros-especiales/{vid}", headers=RF).json()
    assert completo["nombre_paciente"] == "Ana" and completo["datos_personales_visibles"]
    restringido = client.get(f"/registros-especiales/{vid}", headers=CAJERO).json()
    assert restringido["nombre_paciente"] is None and restringido["nombre_medico"] is None
    assert restringido["folio_receta"] == "R-1"
    assert client.get("/registros-especiales", headers=ALM).status_code == 403
    assert client.get("/registros-especiales", headers=COMPRAS).status_code == 403
    lista = client.get("/registros-especiales", headers=RF, params={"resultado": "ACEPTADA"})
    assert lista.status_code == 200 and len(lista.json()) == 1
    assert "restringidos" in client.get("/registros-especiales", headers=CAJERO).json()[0][
        "mensaje"]
    assert client.get("/registros-especiales/NOPE", headers=RF).status_code == 404


def test_us18_reportes_api(client):
    r = client.get("/reportes/caducidad", headers=RF, params={"estado": "CADUCADO"})
    assert r.status_code == 200 and r.json()["total"] == 1
    assert r.json()["filas"][0]["lote_id"] == "LOT-004" and "1 registro" in r.json()["mensaje"]
    r = client.get("/reportes/caducidad", headers=ALM, params={
        "sucursal_id": "SUC-02", "desde": "2026-01-01", "hasta": "2030-12-31"})
    assert r.status_code == 200 and r.json()["total"] == 2
    for tipo in ("retiros", "diferencias", "ajustes", "solicitudes"):
        assert client.get(f"/reportes/{tipo}", headers=COMPRAS).json()["total"] == 0
    assert client.get("/reportes/caducidad", headers=CAJERO).status_code == 403
    assert client.get("/reportes/ventas", headers=RF).status_code == 400   # tipo fuera de lista
    assert client.get("/reportes/caducidad").status_code == 401
