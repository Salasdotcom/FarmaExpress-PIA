"""Consistencia del análisis con el repositorio: 18 US en Gherkin, glosario y trazabilidad."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
FEATURES = sorted((RAIZ / "docs" / "analisis" / "features").glob("US*.feature"))


def test_hay_18_historias_en_gherkin_bien_formadas():
    assert [f.name[:4] for f in FEATURES] == [f"US{i:02d}" for i in range(1, 19)]
    for f in FEATURES:
        t = f.read_text(encoding="utf-8")
        assert t.startswith("# language: es") and "Característica:" in t
        assert t.count("Escenario:") >= 2
        for escenario in t.split("Escenario:")[1:]:
            assert "Dado " in escenario and "Cuando " in escenario and "Entonces " in escenario


def test_cada_historia_esta_en_la_trazabilidad_y_la_matriz():
    traz = (RAIZ / "docs" / "trazabilidad.md").read_text(encoding="utf-8")
    for i in range(1, 19):
        assert re.search(rf"US{i:02d}\b", traz) or f"US{i:02d}" in traz, f"US{i:02d}"
    assert "Pendiente" not in traz


def test_glosario_tiene_53_terminos():
    g = (RAIZ / "docs" / "analisis" / "glosario.md").read_text(encoding="utf-8")
    assert len(re.findall(r"^\| \d+ \|", g, flags=re.M)) == 53


def test_openapi_exportado_cubre_las_historias_nuevas():
    import json
    texto = (RAIZ / "docs" / "api" / "openapi.json").read_text(encoding="utf-8")
    paths = json.loads(texto)["paths"]
    for ruta in ("/ventas/{venta_id}/sustituciones", "/registros-especiales", "/reportes/{tipo}"):
        assert ruta in paths


def test_bpmn_publicados():
    from pathlib import Path
    d = Path("docs/architecture/bpmn")
    for pm in ("02", "03", "07", "08", "09", "10", "11", "12"):
        assert list(d.glob(f"PM-{pm}_*.bpmn")) and list(d.glob(f"PM-{pm}_*.svg"))
