import json
import os

import pytest

import app.services.scenario_comparator as sc


def _make_sim(tmp_path, sim_id, actions=100, names=("A", "B"), event=""):
    d = tmp_path / "simulations" / sim_id
    d.mkdir(parents=True)
    (d / "run_state.json").write_text(json.dumps({
        "total_actions_count": actions,
        "twitter_actions_count": actions // 2,
        "reddit_actions_count": actions - actions // 2,
        "total_rounds": 15,
    }), encoding="utf-8")
    (d / "reddit_profiles.json").write_text(
        json.dumps([{"name": n, "user_id": i} for i, n in enumerate(names)]),
        encoding="utf-8",
    )
    (d / "simulation_config.json").write_text(
        json.dumps({"simulation_requirement": "req"}), encoding="utf-8"
    )
    if event:
        (d / "scenario.json").write_text(
            json.dumps({"scenario_event": event}), encoding="utf-8"
        )


def _make_report(tmp_path, sim_id, text="informe con hallazgos"):
    rid = f"report_{sim_id}"
    d = tmp_path / "reports" / rid
    d.mkdir(parents=True)
    (d / "meta.json").write_text(
        json.dumps({"simulation_id": sim_id}), encoding="utf-8"
    )
    (d / "full_report.md").write_text(text, encoding="utf-8")


class _FakeLLM:
    def __init__(self, *a, **k):
        pass

    def chat(self, *a, **k):
        return "# Comparativa\n| métrica | E1 | E2 |\nRecomendación..."


def _patch_dirs(monkeypatch, tmp_path):
    monkeypatch.setattr(sc, "SIMULATIONS_DIR", str(tmp_path / "simulations"))
    monkeypatch.setattr(sc, "REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setattr(sc, "COMPARISONS_DIR", str(tmp_path / "comparisons"))
    monkeypatch.setattr(sc, "LLMClient", _FakeLLM)


def test_compare_generates_and_persists(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    _make_sim(tmp_path, "sim-a", actions=300, event="evento A")
    _make_sim(tmp_path, "sim-b", actions=150, event="evento B")
    _make_report(tmp_path, "sim-a")
    _make_report(tmp_path, "sim-b")

    result = sc.compare_scenarios(["sim-a", "sim-b"], label="pricing")

    assert result["same_population"] is True
    assert result["content"].startswith("# Comparativa")
    cmp_dir = tmp_path / "comparisons" / result["comparison_id"]
    assert (cmp_dir / "comparison.md").exists()
    meta = json.loads((cmp_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["simulation_ids"] == ["sim-a", "sim-b"]
    assert meta["metrics"][0]["total_actions"] == 300
    assert meta["metrics"][0]["scenario_event"] == "evento A"


def test_compare_detects_different_populations(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    _make_sim(tmp_path, "sim-a", names=("A", "B"))
    _make_sim(tmp_path, "sim-b", names=("A", "C"))
    _make_report(tmp_path, "sim-a")
    _make_report(tmp_path, "sim-b")

    result = sc.compare_scenarios(["sim-a", "sim-b"])
    assert result["same_population"] is False


def test_compare_requires_reports(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    _make_sim(tmp_path, "sim-a")
    _make_sim(tmp_path, "sim-b")
    _make_report(tmp_path, "sim-a")
    # sim-b sin informe
    with pytest.raises(ValueError, match="sin informe"):
        sc.compare_scenarios(["sim-a", "sim-b"])


def test_compare_requires_two_sims(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    with pytest.raises(ValueError):
        sc.compare_scenarios(["solo-uno"])
