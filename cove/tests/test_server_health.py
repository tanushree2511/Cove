import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from server import app
from vision_config import CONFIG


def test_health_endpoint_degraded():
    with patch.object(CONFIG, "skip_model_load", True):
        client = TestClient(app)
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["models"]["pool_size"] >= 1
