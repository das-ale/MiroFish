"""Procedencia de hechos del grafo: documento vs simulación.

Los episodios de documentos entran al grafo durante la construcción
(GraphBuilder). Los episodios de actividad simulada solo entran después de
que arranque el primer ZepGraphMemoryUpdater de ese grafo. Persistiendo ese
instante por grafo, cualquier hecho (edge) puede clasificarse por su
created_at sin llamadas extra a Zep:

    created_at <  first_simulation_at  -> 'document'   (extraído de fuentes)
    created_at >= first_simulation_at  -> 'simulation' (producto de la simulación)

Esto evita presentar como hechos reales afirmaciones que los agentes
inventaron durante la simulación (p. ej. métricas de empresa fabricadas), y
detecta grafos contaminados por simulaciones previas.
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .logger import get_logger

logger = get_logger('mirofish.graph_provenance')

_META_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'uploads', 'graph_meta'
)
_lock = threading.Lock()
_cache: Dict[str, Optional[datetime]] = {}

ORIGIN_DOCUMENT = 'document'
ORIGIN_SIMULATION = 'simulation'

# Etiquetas compactas que ven los LLM del ReportAgent
ORIGIN_TAGS = {
    ORIGIN_DOCUMENT: '[DOC]',
    ORIGIN_SIMULATION: '[SIM]',
}


def _meta_path(graph_id: str) -> str:
    safe = "".join(c for c in graph_id if c.isalnum() or c in ('_', '-'))
    return os.path.join(_META_DIR, f"{safe}.json")


def record_first_simulation(graph_id: str) -> None:
    """Marca (una sola vez) el inicio de la primera simulación del grafo."""
    if not graph_id:
        return
    with _lock:
        path = _meta_path(graph_id)
        if os.path.exists(path):
            return
        try:
            os.makedirs(_META_DIR, exist_ok=True)
            payload = {
                "graph_id": graph_id,
                "first_simulation_at": datetime.now(timezone.utc).isoformat(),
            }
            tmp = f"{path}.tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
            _cache.pop(graph_id, None)
            logger.info(
                f"Registrado inicio de primera simulación del grafo "
                f"{graph_id}: {payload['first_simulation_at']}"
            )
        except Exception as error:
            logger.warning(f"No se pudo registrar marca de simulación: {error}")


def get_first_simulation_at(graph_id: str) -> Optional[datetime]:
    """Instante de la primera simulación del grafo, o None si nunca simuló."""
    if not graph_id:
        return None
    if graph_id in _cache:
        return _cache[graph_id]
    value: Optional[datetime] = None
    try:
        path = _meta_path(graph_id)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                raw = json.load(f).get("first_simulation_at")
            if raw:
                value = _parse_dt(raw)
    except Exception as error:
        logger.warning(f"No se pudo leer marca de simulación: {error}")
    _cache[graph_id] = value
    return value


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def classify_origin(created_at: Any, graph_id: str) -> Optional[str]:
    """'document' | 'simulation' | None (indeterminable)."""
    marker = get_first_simulation_at(graph_id)
    if marker is None:
        # El grafo nunca simuló: todo procede de las fuentes.
        return ORIGIN_DOCUMENT
    created = _parse_dt(created_at)
    if created is None:
        return None
    return ORIGIN_SIMULATION if created >= marker else ORIGIN_DOCUMENT


def tag_fact(fact: str, created_at: Any, graph_id: str) -> str:
    """Antepone [DOC]/[SIM] al hecho si su origen es determinable."""
    origin = classify_origin(created_at, graph_id)
    tag = ORIGIN_TAGS.get(origin)
    return f"{tag} {fact}" if tag else fact
