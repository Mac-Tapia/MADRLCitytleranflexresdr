"""Carga del modelo MADRL ganador exportado a ONNX para el servicio de inferencia.

Contrato esperado (producido por un futuro `tools/training/export_winning_model_onnx.py`
una vez seleccionado el mejor agente vía KPIEvaluator/HPHI sobre las 12
corridas oficiales — 4 algoritmos x 3 escenarios E1/E2/E3):

- ``MODEL_PATH`` (.onnx): grafo de inferencia del actor (observaciones -> acciones).
  Entrada: tensor float32 de forma ``(n_agents, obs_dim)`` o ``(1, bact_dim)``
  según si el agente es descentralizado (HAPPO/MATD3/MAAC, por edificio) o
  centralizado (BACTTensor 29D, ver `uc3m/env/bact.py`).
- ``MODEL_METADATA_PATH`` (.json): metadatos del checkpoint —
  ``{"algorithm": "happo", "scenario": "E1", "obs_dim": ..., "action_dim": ...,
    "n_agents": 17, "central_agent": false, "action_space": {...},
    "normalization": {"mean": [...], "std": [...]}}``.

Si los archivos no existen, ``ModelBundle.load`` cae a un modo "stub"
(política aleatoria dentro del espacio de acciones) para permitir levantar
el stack de demo end-to-end sin un checkpoint real.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("inference.model_loader")


@dataclass
class ModelMetadata:
    algorithm: str
    scenario: str
    obs_dim: int
    action_dim: int
    n_agents: int
    central_agent: bool
    action_low: np.ndarray
    action_high: np.ndarray
    norm_mean: np.ndarray | None = None
    norm_std: np.ndarray | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ModelMetadata":
        action_space = d.get("action_space", {})
        low = np.asarray(action_space.get("low", [-1.0]), dtype=np.float32)
        high = np.asarray(action_space.get("high", [1.0]), dtype=np.float32)
        norm = d.get("normalization") or {}
        mean = np.asarray(norm["mean"], dtype=np.float32) if "mean" in norm else None
        std = np.asarray(norm["std"], dtype=np.float32) if "std" in norm else None
        return cls(
            algorithm=d.get("algorithm", "unknown"),
            scenario=d.get("scenario", "unknown"),
            obs_dim=int(d.get("obs_dim", 29)),
            action_dim=int(d.get("action_dim", 1)),
            n_agents=int(d.get("n_agents", 17)),
            central_agent=bool(d.get("central_agent", False)),
            action_low=low,
            action_high=high,
            norm_mean=mean,
            norm_std=std,
        )


class ModelBundle:
    """Wraps an ONNX Runtime session (or a stub policy) for /act."""

    def __init__(self, session: Any | None, metadata: ModelMetadata, is_stub: bool):
        self.session = session
        self.metadata = metadata
        self.is_stub = is_stub

    @classmethod
    def load(cls, model_path: str | os.PathLike, metadata_path: str | os.PathLike) -> "ModelBundle":
        model_path = Path(model_path)
        metadata_path = Path(metadata_path)

        if metadata_path.is_file():
            metadata = ModelMetadata.from_dict(json.loads(metadata_path.read_text(encoding="utf-8")))
        else:
            logger.warning("Metadata file not found at %s — using stub metadata.", metadata_path)
            metadata = ModelMetadata.from_dict({})

        if model_path.is_file():
            try:
                import onnxruntime as ort

                session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
                logger.info("Loaded ONNX model from %s (algorithm=%s, scenario=%s)",
                            model_path, metadata.algorithm, metadata.scenario)
                return cls(session=session, metadata=metadata, is_stub=False)
            except Exception:
                logger.exception("Failed to load ONNX model from %s — falling back to stub policy.", model_path)

        logger.warning("No usable model at %s — serving stub (random) policy for demo purposes.", model_path)
        return cls(session=None, metadata=metadata, is_stub=True)

    def act(self, observations: np.ndarray) -> np.ndarray:
        """Compute actions for a batch of observations.

        ``observations`` shape: ``(n_agents, obs_dim)`` for decentralized
        agents, or ``(1, obs_dim)`` for a centralized BACT-style agent.
        Returns actions of shape ``(n_agents, action_dim)`` clipped to the
        declared action space.
        """
        meta = self.metadata
        if self.session is not None:
            x = observations.astype(np.float32)
            if meta.norm_mean is not None and meta.norm_std is not None:
                x = (x - meta.norm_mean) / np.where(meta.norm_std == 0, 1.0, meta.norm_std)
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: x})
            actions = np.asarray(outputs[0], dtype=np.float32)
        else:
            n = observations.shape[0]
            rng = np.random.default_rng(0)
            actions = rng.uniform(
                low=meta.action_low,
                high=meta.action_high,
                size=(n, meta.action_dim),
            ).astype(np.float32)

        return np.clip(actions, meta.action_low, meta.action_high)
