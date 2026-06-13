"""Servicio de inferencia FastAPI para el agente MADRL ganador (demo Fase 8).

Endpoints:
- GET  /health      -> liveness/readiness probe
- GET  /model/info  -> metadatos del modelo cargado (algoritmo, escenario, dims)
- POST /act         -> {"observations": [[...], ...]} -> {"actions": [[...], ...]}

Ejecutar localmente:
    uvicorn app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from model_loader import ModelBundle

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "info").upper())
logger = logging.getLogger("inference.app")

MODEL_PATH = os.environ.get("MODEL_PATH", "/models/winning_agent.onnx")
MODEL_METADATA_PATH = os.environ.get("MODEL_METADATA_PATH", "/models/winning_agent.metadata.json")

app = FastAPI(title="MADRL Iquitos — Inference Service", version="0.1.0")
_bundle: ModelBundle | None = None


@app.on_event("startup")
def _load_model() -> None:
    global _bundle
    _bundle = ModelBundle.load(MODEL_PATH, MODEL_METADATA_PATH)


class ActRequest(BaseModel):
    observations: list[list[float]] = Field(..., description="Shape (n_agents, obs_dim)")


class ActResponse(BaseModel):
    actions: list[list[float]]
    algorithm: str
    scenario: str
    is_stub: bool


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": _bundle is not None and not _bundle.is_stub}


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

    obs = np.asarray(request.observations, dtype=np.float32)
    if obs.ndim != 2:
        raise HTTPException(status_code=422, detail="observations must be a 2D array (n_agents, obs_dim)")

    try:
        actions = _bundle.act(obs)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc

    return ActResponse(
        actions=actions.tolist(),
        algorithm=_bundle.metadata.algorithm,
        scenario=_bundle.metadata.scenario,
        is_stub=_bundle.is_stub,
    )
