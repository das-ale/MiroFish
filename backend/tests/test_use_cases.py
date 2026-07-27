import pytest

from app.use_cases import (
    USE_CASES, get_report_instructions, list_use_cases,
    render_requirement, render_scenario_event,
)


def test_three_use_cases_exposed_with_form_fields():
    listed = list_use_cases()
    assert {u["id"] for u in listed} == {"price_test", "ad_test", "launch_test"}
    for u in listed:
        assert u["form_fields"], u["id"]
        assert all("key" in f and "label" in f for f in u["form_fields"])


def test_ad_requirement_contains_verbatim_rule_and_copy():
    req = render_requirement("ad_test", {
        "brand": "Marea", "headline": "Titular X", "copy": "COPY LITERAL AQUI",
        "creative_description": "foto", "cta_offer": "Reserva",
        "audience": "familias",
    })
    assert "COPY LITERAL AQUI" in req
    assert "TEXTO EXACTO" in req  # regla verbatim
    assert "Marea" in req


def test_missing_inputs_fill_placeholder():
    req = render_requirement("price_test", {"product": "SaaS"})
    assert "(no especificado)" in req
    assert "SaaS" in req


def test_report_instructions_fix_outline_and_verdict():
    for uid in USE_CASES:
        instr = get_report_instructions(uid)
        assert "Veredicto" in instr
        assert "GO" in instr and "AJUSTAR" in instr
        assert "Limitaciones" in instr
    assert get_report_instructions(None) is None
    assert get_report_instructions("nope") is None


def test_scenario_event_templates_render():
    ev = render_scenario_event("launch_test", {
        "brand": "Clinica Sol", "launch": "apertura", "message": "Abrimos",
        "channel_date": "IG septiembre", "audience": "Málaga",
    })
    assert "Clinica Sol" in ev and "Abrimos" in ev
