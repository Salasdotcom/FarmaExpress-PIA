from fastapi.testclient import TestClient

from src.api.main import app


def test_health_y_openapi():
    c = TestClient(app)
    assert c.get("/health").json() == {"status": "ok"}
    assert c.get("/openapi.json").status_code == 200
