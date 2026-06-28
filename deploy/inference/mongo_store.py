"""Capa de persistencia y análisis opcional sobre MongoDB para el servicio de inferencia.

Diseño tolerante a fallos para una demo de operatividad:

- El import de :mod:`pymongo` y la conexión al servidor son PEREZOSOS: solo se
  intentan la primera vez que se necesitan.
- Si ``pymongo`` no está instalado, o si Mongo no responde, la persistencia
  queda DESACTIVADA y el servicio de inferencia sigue funcionando con normalidad
  (modo stub o modelo real). Nunca se propaga una excepción al request de ``/act``.

Variables de entorno:
- ``MONGODB_URI`` (p.ej. ``mongodb://mongo:27017``). Si no está definida, la
  persistencia queda desactivada.
- ``MONGODB_DB``  (por defecto ``madrl``).
- ``MONGODB_COLLECTION`` (por defecto ``inferences``).
- ``MONGODB_TIMEOUT_MS`` (timeout de selección de servidor; por defecto ``1500``).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger("inference.mongo_store")


class MongoStore:
    """Cliente perezoso y tolerante a fallos para persistir y analizar inferencias.

    La instancia siempre puede crearse; la conexión real se difiere hasta el
    primer uso (:meth:`_collection`). Cualquier fallo deja ``enabled`` en
    ``False`` sin lanzar excepciones hacia los endpoints.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        db_name: Optional[str] = None,
        collection_name: Optional[str] = None,
        timeout_ms: Optional[int] = None,
    ) -> None:
        self.uri = uri if uri is not None else os.environ.get("MONGODB_URI")
        self.db_name = db_name or os.environ.get("MONGODB_DB", "madrl")
        self.collection_name = collection_name or os.environ.get(
            "MONGODB_COLLECTION", "inferences"
        )
        self.timeout_ms = int(
            timeout_ms
            if timeout_ms is not None
            else os.environ.get("MONGODB_TIMEOUT_MS", "1500")
        )
        self._client: Any | None = None
        self._initialized = False
        # ``None`` => aún no se intentó; ``True/False`` => resultado conocido.
        self._available: Optional[bool] = None

    # -- estado ------------------------------------------------------------
    @property
    def configured(self) -> bool:
        """``True`` si hay una ``MONGODB_URI`` configurada (no implica conexión)."""
        return bool(self.uri)

    @property
    def enabled(self) -> bool:
        """``True`` si la persistencia está configurada y la última conexión fue exitosa."""
        if not self.configured:
            return False
        coll = self._collection()
        return coll is not None

    # -- conexión perezosa -------------------------------------------------
    def _collection(self) -> Any | None:
        """Devuelve la colección de Mongo o ``None`` si no está disponible.

        Inicializa el cliente de forma perezosa la primera vez y cachea el
        resultado. Nunca lanza: ante cualquier error registra un warning y
        deja la persistencia desactivada.
        """
        if not self.configured:
            return None

        if not self._initialized:
            self._initialized = True
            try:
                from pymongo import MongoClient  # import perezoso

                self._client = MongoClient(
                    self.uri,
                    serverSelectionTimeoutMS=self.timeout_ms,
                    connectTimeoutMS=self.timeout_ms,
                )
                # Forzamos una comprobación de conectividad temprana.
                self._client.admin.command("ping")
                self._available = True
                logger.info(
                    "MongoDB persistence enabled (uri=%s, db=%s, collection=%s).",
                    self.uri,
                    self.db_name,
                    self.collection_name,
                )
            except ImportError:
                self._available = False
                logger.warning(
                    "pymongo no está instalado — persistencia MongoDB desactivada."
                )
            except Exception as exc:  # pragma: no cover - depende de entorno
                self._available = False
                logger.warning(
                    "No se pudo conectar a MongoDB (%s) — persistencia desactivada: %s",
                    self.uri,
                    exc,
                )

        if not self._available or self._client is None:
            return None

        try:
            return self._client[self.db_name][self.collection_name]
        except Exception as exc:  # pragma: no cover - defensivo
            logger.warning("Acceso a colección MongoDB falló: %s", exc)
            return None

    # -- escritura ---------------------------------------------------------
    def record_inference(
        self,
        *,
        algorithm: str,
        scenario: str,
        is_stub: bool,
        observations: list[list[float]],
        actions: list[list[float]],
        latency_ms: Optional[float] = None,
    ) -> None:
        """Inserta un documento con el resultado de una inferencia.

        No bloqueante ante errores: cualquier fallo de escritura se registra
        como warning y se ignora para no tumbar el request de ``/act``.
        """
        coll = self._collection()
        if coll is None:
            return

        document = {
            "timestamp": datetime.now(timezone.utc),
            "algorithm": algorithm,
            "scenario": scenario,
            "is_stub": bool(is_stub),
            "n_agents": len(observations),
            "observations": observations,
            "actions": actions,
        }
        if latency_ms is not None:
            document["latency_ms"] = float(latency_ms)

        try:
            coll.insert_one(document)
        except Exception as exc:  # pragma: no cover - depende de entorno
            logger.warning("No se pudo persistir la inferencia en MongoDB: %s", exc)

    # -- análisis ----------------------------------------------------------
    def summary(self) -> dict:
        """Estadísticas agregadas calculadas con un pipeline de agregación.

        Devuelve ``{"persistence": "disabled"}`` si Mongo no está disponible.
        """
        coll = self._collection()
        if coll is None:
            return {"persistence": "disabled"}

        try:
            total = coll.count_documents({})
            if total == 0:
                return {
                    "persistence": "enabled",
                    "total_inferences": 0,
                    "by_algorithm": {},
                    "stub_pct": None,
                    "real_pct": None,
                    "action_magnitude": None,
                    "first_timestamp": None,
                    "last_timestamp": None,
                }

            by_algorithm = {
                doc["_id"]: doc["count"]
                for doc in coll.aggregate(
                    [{"$group": {"_id": "$algorithm", "count": {"$sum": 1}}}]
                )
            }

            stub_count = coll.count_documents({"is_stub": True})
            real_count = total - stub_count

            # Magnitud de acción = valor absoluto de cada componente, agregado
            # sobre todos los documentos. Se "desenrolla" el array anidado.
            mag_cursor = list(
                coll.aggregate(
                    [
                        {"$unwind": "$actions"},
                        {"$unwind": "$actions"},
                        {"$project": {"abs_action": {"$abs": "$actions"}}},
                        {
                            "$group": {
                                "_id": None,
                                "mean": {"$avg": "$abs_action"},
                                "min": {"$min": "$abs_action"},
                                "max": {"$max": "$abs_action"},
                            }
                        },
                    ]
                )
            )
            action_magnitude = None
            if mag_cursor:
                m = mag_cursor[0]
                action_magnitude = {
                    "mean": m.get("mean"),
                    "min": m.get("min"),
                    "max": m.get("max"),
                }

            ts_bounds = list(
                coll.aggregate(
                    [
                        {
                            "$group": {
                                "_id": None,
                                "first": {"$min": "$timestamp"},
                                "last": {"$max": "$timestamp"},
                            }
                        }
                    ]
                )
            )
            first_ts = last_ts = None
            if ts_bounds:
                first_ts = _iso(ts_bounds[0].get("first"))
                last_ts = _iso(ts_bounds[0].get("last"))

            return {
                "persistence": "enabled",
                "total_inferences": total,
                "by_algorithm": by_algorithm,
                "stub_pct": round(100.0 * stub_count / total, 2),
                "real_pct": round(100.0 * real_count / total, 2),
                "action_magnitude": action_magnitude,
                "first_timestamp": first_ts,
                "last_timestamp": last_ts,
            }
        except Exception as exc:  # pragma: no cover - depende de entorno
            logger.warning("Fallo al calcular summary desde MongoDB: %s", exc)
            return {"persistence": "disabled", "error": str(exc)}

    def recent(self, limit: int = 10) -> dict:
        """Últimas ``limit`` inferencias, resumidas (sin volcar arrays gigantes)."""
        coll = self._collection()
        if coll is None:
            return {"persistence": "disabled"}

        limit = max(1, min(int(limit), 200))
        try:
            cursor = coll.find(
                {},
                projection={
                    "observations": False,
                    "actions": False,
                },
            ).sort("timestamp", -1).limit(limit)

            items = []
            for doc in cursor:
                items.append(
                    {
                        "id": str(doc.get("_id")),
                        "timestamp": _iso(doc.get("timestamp")),
                        "algorithm": doc.get("algorithm"),
                        "scenario": doc.get("scenario"),
                        "is_stub": doc.get("is_stub"),
                        "n_agents": doc.get("n_agents"),
                        "latency_ms": doc.get("latency_ms"),
                    }
                )
            return {"persistence": "enabled", "count": len(items), "items": items}
        except Exception as exc:  # pragma: no cover - depende de entorno
            logger.warning("Fallo al leer recientes desde MongoDB: %s", exc)
            return {"persistence": "disabled", "error": str(exc)}

    def close(self) -> None:
        """Cierra el cliente de Mongo si existe (idempotente)."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:  # pragma: no cover - defensivo
                pass


def _iso(value: Any) -> Optional[str]:
    """Convierte un ``datetime`` a ISO-8601 (UTC) o devuelve ``None``."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return None
