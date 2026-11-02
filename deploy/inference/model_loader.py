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

Sin un modelo cargable ``ModelBundle.load`` devuelve ``None`` (servicio vivo
pero no listo). La política "stub" (aleatoria dentro del espacio de acciones)
existe solo con ``allow_stub=True`` (opt-in explícito del demo) y nunca es
elegible para controlar una planta. Un modelo real tampoco lo es mientras sus
metadatos no declaren ``acceptance.operational_acceptance: true``, que solo
puede venir de una validación operacional independiente (SIL/HIL/piloto).
Observaciones con forma distinta a la declarada o con NaN/Inf se rechazan, y
una salida no finita del modelo nunca se recorta a un setpoint.
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
    operational_acceptance: bool = False

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
            operational_acceptance=(d.get("acceptance") or {}).get("operational_acceptance") is True,
        )


class ModelBundle:
    """Wraps an ONNX Runtime session (or a stub policy) for /act."""

    def __init__(self, session: Any | None, metadata: ModelMetadata, is_stub: bool):
        self.session = session
        self.metadata = metadata
        self.is_stub = is_stub
        self.last_clipped = 0

    @property
    def control_eligible(self) -> bool:
        """Only a real model with independent operational acceptance may drive a plant."""
        return (not self.is_stub and self.session is not None
                and self.metadata.operational_acceptance)

    @classmethod
    def load(cls, model_path: str | os.PathLike, metadata_path: str | os.PathLike, *,
             allow_stub: bool = False) -> "ModelBundle | None":
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
                logger.exception("Failed to load ONNX model from %s.", model_path)

        if not allow_stub:
            logger.warning("No usable model at %s — service is not ready (no stub without opt-in).", model_path)
            return None
        logger.warning("No usable model at %s — serving opt-in stub (random) policy, never control-eligible.",
                       model_path)
        return cls(session=None, metadata=metadata, is_stub=True)

    def validate_observations(self, observations: np.ndarray) -> np.ndarray:
        """Refuse observations that do not match the declared shape or are not finite."""
        meta = self.metadata
        x = np.asarray(observations, dtype=np.float32)
        expected = (1 if meta.central_agent else meta.n_agents, meta.obs_dim)
        if x.ndim != 2 or x.shape != expected:
            raise ValueError(f"observations must have shape {expected}, got {x.shape}")
        if not np.all(np.isfinite(x)):
            raise ValueError("observations must be finite (no NaN/Inf)")
        return x

    def act(self, observations: np.ndarray) -> np.ndarray:
        """Compute actions for a batch of observations.

        ``observations`` shape: ``(n_agents, obs_dim)`` for decentralized
        agents, or ``(1, obs_dim)`` for a centralized BACT-style agent.
        Returns actions of shape ``(n_agents, action_dim)`` clipped to the
        declared action space.
        """
        meta = self.metadata
        observations = self.validate_observations(observations)
        if self.session is not None:
            x = observations.astype(np.float32)
            if meta.norm_mean is not None and meta.norm_std is not None:
                x = (x - meta.norm_mean) / np.where(meta.norm_std == 0, 1.0, meta.norm_std)
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: x})
            actions = np.asarray(outputs[0], dtype=np.float32)
            if not np.all(np.isfinite(actions)):
                raise ValueError("model produced non-finite actions; nothing is clipped into a setpoint")
        else:
            n = observations.shape[0]
            rng = np.random.default_rng(0)
            actions = rng.uniform(
                low=meta.action_low,
                high=meta.action_high,
                size=(n, meta.action_dim),
            ).astype(np.float32)

        clipped = np.clip(actions, meta.action_low, meta.action_high)
        self.last_clipped = int(np.count_nonzero(clipped != actions))
        return clipped
