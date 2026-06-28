"""Tests ligeros del servicio de inferencia (sin MongoDB real).

Verifican que el modo stub y los endpoints de análisis funcionan cuando la
persistencia MongoDB no está configurada/disponible. Se ejecutan con:

    .\\.venv39-citylearn-v3\\Scripts\\python.exe -m pytest deploy/inference/test_app.py
"""
from __future__ import annotations

import os

from fastapi.testclient import TestClient

# Aseguramos que la persistencia quede desactivada (sin MONGODB_URI) antes de
# importar la app, para no intentar conectar a ningún Mongo durante el test.
os.environ.pop("MONGODB_URI", None)
os.environ.setdefault("MODEL_PATH", "/nonexistent/winning_agent.onnx")

from app import app  # noqa: E402


def test_health_ok() -> None:
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


def test_act_stub_returns_actions() -> None:
    with TestClient(app) as client:
        payload = {"observations": [[0.0] * 29, [0.1] * 29]}
        resp = client.post("/act", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_stub"] is True
        assert len(body["actions"]) == 2


def test_analytics_summary_disabled_without_mongo() -> None:
    with TestClient(app) as client:
        resp = client.get("/analytics/summary")
        assert resp.status_code == 200
        assert resp.json() == {"persistence": "disabled"}


def test_analytics_recent_disabled_without_mongo() -> None:
    with TestClient(app) as client:
        resp = client.get("/analytics/recent?limit=5")
        assert resp.status_code == 200
        assert resp.json() == {"persistence": "disabled"}
