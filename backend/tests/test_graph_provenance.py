import json
import os
from datetime import datetime, timedelta, timezone

import app.utils.graph_provenance as gp


def _use_tmp_meta(monkeypatch, tmp_path):
    monkeypatch.setattr(gp, "_META_DIR", str(tmp_path))
    gp._cache.clear()


def test_no_marker_means_everything_is_document(monkeypatch, tmp_path):
    _use_tmp_meta(monkeypatch, tmp_path)
    assert gp.classify_origin("2026-07-26T10:00:00Z", "graph-x") == "document"
    assert gp.tag_fact("hecho", "2026-07-26T10:00:00Z", "graph-x") == "[DOC] hecho"


def test_marker_splits_document_and_simulation(monkeypatch, tmp_path):
    _use_tmp_meta(monkeypatch, tmp_path)
    gp.record_first_simulation("graph-y")
    marker = gp.get_first_simulation_at("graph-y")
    assert marker is not None

    before = (marker - timedelta(hours=1)).isoformat()
    after = (marker + timedelta(hours=1)).isoformat()

    assert gp.classify_origin(before, "graph-y") == "document"
    assert gp.classify_origin(after, "graph-y") == "simulation"
    assert gp.tag_fact("f", before, "graph-y").startswith("[DOC]")
    assert gp.tag_fact("f", after, "graph-y").startswith("[SIM]")


def test_marker_is_recorded_only_once(monkeypatch, tmp_path):
    _use_tmp_meta(monkeypatch, tmp_path)
    gp.record_first_simulation("graph-z")
    first = gp.get_first_simulation_at("graph-z")
    gp._cache.clear()
    gp.record_first_simulation("graph-z")  # segunda simulación: no sobrescribe
    assert gp.get_first_simulation_at("graph-z") == first


def test_unparseable_created_at_yields_untagged_fact(monkeypatch, tmp_path):
    _use_tmp_meta(monkeypatch, tmp_path)
    gp.record_first_simulation("graph-w")
    assert gp.classify_origin("no-es-fecha", "graph-w") is None
    assert gp.classify_origin(None, "graph-w") is None
    assert gp.tag_fact("hecho", None, "graph-w") == "hecho"


def test_datetime_objects_and_naive_dates_are_handled(monkeypatch, tmp_path):
    _use_tmp_meta(monkeypatch, tmp_path)
    gp.record_first_simulation("graph-v")
    marker = gp.get_first_simulation_at("graph-v")
    aware = marker + timedelta(minutes=5)
    assert gp.classify_origin(aware, "graph-v") == "simulation"
