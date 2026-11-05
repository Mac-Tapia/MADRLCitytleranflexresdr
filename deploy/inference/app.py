"""Servicio de inferencia FastAPI para el agente MADRL ganador (demo Fase 8).

Endpoints:
- GET  /health              -> liveness probe (+ ready / operational_ready flags)
- GET  /ready               -> 200 solo con un modelo real cargado; 503 si no hay modelo o es stub
- GET  /model/info          -> metadatos del modelo cargado (algoritmo, escenario, dims)
- POST /act                 -> {"observations": [[...], ...]} -> {"actions": [[...], ...]}
- GET  /analytics/summary   -> estadísticas agregadas desde MongoDB (si está disponible)
- GET  /analytics/recent    -> últimas inferencias persistidas (resumidas)

Persistencia opcional: si ``MONGODB_URI`` apunta a un MongoDB accesible y
``pymongo`` está instalado, cada ``/act`` se registra en la colección
``inferences``. Si no, la persistencia queda desactivada sin afectar al servicio.

Cercado del demo: sin modelo el servicio vive pero no está listo; la política
stub solo existe con ``INFERENCE_DEMO_STUB=1`` y nunca es ``control_eligible``.
``operational_ready`` es siempre falso aquí: la aceptación operacional (SIL/HIL,
piloto, seguridad OT) es independiente de este servicio.

Ejecutar localmente:
    uvicorn app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os
import time

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from model_loader import ModelBundle
from mongo_store import MongoStore

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "info").upper())
logger = logging.getLogger("inference.app")

DEFAULT_MODEL_PATH = "/models/winning_agent.onnx"
DEFAULT_MODEL_METADATA_PATH = "/models/winning_agent.metadata.json"

app = FastAPI(title="MADRL Iquitos — Inference Service", version="0.1.0")
_bundle: ModelBundle | None = None
# Cliente de persistencia perezoso y tolerante a fallos (ver mongo_store.py).
_store = MongoStore()


@app.on_event("startup")
def _load_model() -> None:
    global _bundle
    _bundle = ModelBundle.load(
        os.environ.get("MODEL_PATH", DEFAULT_MODEL_PATH),
        os.environ.get("MODEL_METADATA_PATH", DEFAULT_MODEL_METADATA_PATH),
        allow_stub=os.environ.get("INFERENCE_DEMO_STUB") == "1",
    )


@app.on_event("shutdown")
def _close_store() -> None:
    _store.close()


class ActRequest(BaseModel):
    observations: list[list[float]] = Field(..., description="Shape (n_agents, obs_dim)")


class ActResponse(BaseModel):
    actions: list[list[float]]
    algorithm: str
    scenario: str
    is_stub: bool
    control_eligible: bool
    clipped_actions: int


def _ready() -> bool:
    return _bundle is not None and not _bundle.is_stub


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": _ready(), "ready": _ready(),
            "stub": _bundle is not None and _bundle.is_stub,
            "operational_ready": False,
            "operational_note": "operational acceptance is an independent SIL/HIL/pilot step, not this service"}


@app.get("/ready")
def ready() -> dict:
    if not _ready():
        raise HTTPException(status_code=503, detail="No accepted model loaded (stub or missing)")
    return {"ready": True, "control_eligible": _bundle.control_eligible}


@app.get("/model/info")
def model_info() -> dict:
    if _bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    meta = _bundle.metadata
    return {
        "algorithm": meta.algorithm,
        "scenario": meta.scenario,
        "obs_dim": meta.obs_dim,
        "action_dim": meta.action_dim,
        "n_agents": meta.n_agents,
        "central_agent": meta.central_agent,
        "is_stub": _bundle.is_stub,
    }


@app.post("/act", response_model=ActResponse)
def act(request: ActRequest) -> ActResponse:
    if _bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        obs = _bundle.validate_observations(np.asarray(request.observations, dtype=np.float32))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    started = time.perf_counter()
    try:
        result = _bundle.act_with_diagnostics(obs)
    except Exception as exc:
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail="Inference failed") from exc
    latency_ms = (time.perf_counter() - started) * 1000.0

    actions_list = result.actions.tolist()

    # Persistencia no bloqueante: nunca tumba el request si Mongo falla.
    _store.record_inference(
        algorithm=_bundle.metadata.algorithm,
        scenario=_bundle.metadata.scenario,
        is_stub=_bundle.is_stub,
        observations=request.observations,
        actions=actions_list,
        latency_ms=latency_ms,
    )

    return ActResponse(
        actions=actions_list,
        algorithm=_bundle.metadata.algorithm,
        scenario=_bundle.metadata.scenario,
        is_stub=_bundle.is_stub,
        control_eligible=_bundle.control_eligible,
        clipped_actions=result.clipped_actions,
    )


@app.get("/analytics/summary")
def analytics_summary() -> dict:
    """Estadísticas agregadas de las inferencias persistidas en MongoDB.

    Devuelve ``{"persistence": "disabled"}`` con HTTP 200 si Mongo no está
    configurado/disponible.
    """
    return _store.summary()


@app.get("/analytics/recent")
def analytics_recent(limit: int = 10) -> dict:
    """Últimas ``limit`` inferencias persistidas (resumidas, sin arrays grandes)."""
    return _store.recent(limit=limit)
