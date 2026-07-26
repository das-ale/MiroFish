import app.utils.llm_client as llm_client_module

from app.services.oasis_profile_generator import OasisProfileGenerator
from app.services.zep_entity_reader import EntityNode


def _entity(name: str, label: str = "Person", summary: str = "") -> EntityNode:
    return EntityNode(
        uuid=f"uuid-{name}",
        name=name,
        labels=[label],
        summary=summary,
        attributes={},
    )


def _generator() -> OasisProfileGenerator:
    generator = object.__new__(OasisProfileGenerator)
    generator.api_key = "test-key"
    generator.base_url = "http://localhost/test"
    generator.model_name = "test-model"
    return generator


class _FakeLLM:
    response = {"exclusions": []}
    raise_error = False

    def __init__(self, *args, **kwargs):
        pass

    def chat_json(self, *args, **kwargs):
        if _FakeLLM.raise_error:
            raise RuntimeError("llm down")
        return _FakeLLM.response


def _patch_llm(monkeypatch, response=None, raise_error=False):
    _FakeLLM.response = response or {"exclusions": []}
    _FakeLLM.raise_error = raise_error
    monkeypatch.setattr(llm_client_module, "LLMClient", _FakeLLM)


def test_filter_excludes_platforms_and_referenced_people(monkeypatch):
    entities = [
        _entity("Antonio Vargas", "RestaurantOwner"),
        _entity("LinkedIn", "Organization", "Professional social platform"),
        _entity("Hormozi", "Person", "Influencer followed by local owners"),
        _entity("Asociación de Vecinos", "NeighborhoodAssociation"),
    ]
    _patch_llm(monkeypatch, {
        "exclusions": [
            {"name": "LinkedIn", "reason": "platform_or_tool", "why": "platform"},
            {"name": "Hormozi", "reason": "referenced_person", "why": "only cited"},
        ]
    })

    kept, excluded = _generator().classify_actor_entities(entities, "req")

    assert [e.name for e in kept] == ["Antonio Vargas", "Asociación de Vecinos"]
    assert {e["name"] for e in excluded} == {"LinkedIn", "Hormozi"}
    assert all(e["reason"] in (
        "platform_or_tool", "referenced_person", "abstract_concept"
    ) for e in excluded)


def test_filter_fails_open_when_llm_errors(monkeypatch):
    entities = [_entity("A"), _entity("B")]
    _patch_llm(monkeypatch, raise_error=True)

    kept, excluded = _generator().classify_actor_entities(entities, "req")

    assert kept == entities
    assert excluded == []


def test_filter_ignores_unknown_names_and_invalid_reasons(monkeypatch):
    entities = [_entity("A"), _entity("B"), _entity("C")]
    _patch_llm(monkeypatch, {
        "exclusions": [
            {"name": "Nadie", "reason": "platform_or_tool", "why": "x"},
            {"name": "A", "reason": "no_me_gusta", "why": "x"},
            "garbage",
        ]
    })

    kept, excluded = _generator().classify_actor_entities(entities, "req")

    assert kept == entities
    assert excluded == []


def test_filter_fails_open_when_excluding_more_than_half(monkeypatch):
    entities = [_entity("A"), _entity("B"), _entity("C"), _entity("D")]
    _patch_llm(monkeypatch, {
        "exclusions": [
            {"name": "A", "reason": "platform_or_tool", "why": "x"},
            {"name": "B", "reason": "platform_or_tool", "why": "x"},
            {"name": "C", "reason": "abstract_concept", "why": "x"},
        ]
    })

    kept, excluded = _generator().classify_actor_entities(entities, "req")

    assert kept == entities
    assert excluded == []


def test_filter_disabled_by_env(monkeypatch):
    entities = [_entity("LinkedIn")]
    monkeypatch.setenv("PROFILE_ENTITY_FILTER", "0")
    _patch_llm(monkeypatch, {
        "exclusions": [
            {"name": "LinkedIn", "reason": "platform_or_tool", "why": "x"},
        ]
    })

    kept, excluded = _generator().classify_actor_entities(entities, "req")

    assert kept == entities
    assert excluded == []
