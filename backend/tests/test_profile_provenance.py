from app.services.oasis_profile_generator import OasisProfileGenerator
from app.services.zep_entity_reader import EntityNode


def _entity(name="Antonio Vargas", label="RestaurantOwner"):
    return EntityNode(
        uuid="uuid-1",
        name=name,
        labels=[label],
        summary="Dueño del restaurante La Marea Azul",
        attributes={},
    )


def _generator():
    generator = object.__new__(OasisProfileGenerator)
    generator.graph_id = None
    generator.zep_client = None
    return generator


def test_llm_profile_marks_observed_inferred_and_synthetic(monkeypatch):
    generator = _generator()
    monkeypatch.setattr(
        OasisProfileGenerator,
        "_build_entity_context",
        lambda self, entity: "ctx",
    )
    monkeypatch.setattr(
        OasisProfileGenerator,
        "_generate_profile_with_llm",
        lambda self, **kwargs: {
            "bio": "Cocinero de 58 años",
            "persona": "Cercano y orgulloso de la calidad",
            "age": 58,
            "profession": "Restaurador",
            # sin gender/country/interested_topics: deben quedar synthetic
        },
    )

    profile = generator.generate_profile_from_entity(
        _entity(), user_id=1, use_llm=True
    )
    prov = profile.provenance

    assert prov["name"] == "observed"
    assert prov["source_entity_type"] == "observed"
    # campos devueltos por el LLM
    for f in ("bio", "persona", "age", "profession"):
        assert prov[f] == "inferred", f
    # campos no devueltos → rellenos
    for f in ("gender", "country", "interested_topics"):
        assert prov[f] == "synthetic", f
    # siempre inventados, venga lo que venga
    for f in (
        "user_name", "karma", "friend_count", "follower_count",
        "statuses_count", "mbti",
    ):
        assert prov[f] == "synthetic", f
    # y viaja en el dict completo
    assert profile.to_dict()["provenance"] == prov


def test_rule_based_profile_marks_everything_synthetic_except_identity(
    monkeypatch,
):
    generator = _generator()
    monkeypatch.setattr(
        OasisProfileGenerator,
        "_build_entity_context",
        lambda self, entity: "ctx",
    )

    profile = generator.generate_profile_from_entity(
        _entity(label="Organization"), user_id=2, use_llm=False
    )
    prov = profile.provenance

    assert prov["name"] == "observed"
    for f in ("bio", "persona", "age", "gender", "country", "profession"):
        assert prov[f] == "synthetic", f


def test_oasis_export_formats_do_not_leak_provenance(monkeypatch):
    generator = _generator()
    monkeypatch.setattr(
        OasisProfileGenerator,
        "_build_entity_context",
        lambda self, entity: "ctx",
    )
    monkeypatch.setattr(
        OasisProfileGenerator,
        "_generate_profile_with_llm",
        lambda self, **kwargs: {"bio": "b", "persona": "p"},
    )
    profile = generator.generate_profile_from_entity(
        _entity(), user_id=3, use_llm=True
    )
    assert "provenance" not in profile.to_reddit_format()
    assert "provenance" not in profile.to_twitter_format()
