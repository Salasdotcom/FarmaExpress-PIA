"""Exporta el contrato OpenAPI a docs/api/openapi.json (python scripts/export_openapi.py)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api.main import app  # noqa: E402

destino = Path(__file__).resolve().parent.parent / "docs" / "api" / "openapi.json"
destino.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False), encoding="utf-8")
print(f"OpenAPI exportado a {destino} ({len(app.openapi()['paths'])} rutas)")
