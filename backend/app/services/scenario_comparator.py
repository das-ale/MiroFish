"""Comparador de escenarios (P3.2).

Toma N simulaciones terminadas (idealmente escenarios sobre el mismo mundo
y población) y produce un informe comparativo orientado a decisión:
métricas duras por escenario + síntesis LLM con tabla, hallazgos
diferenciales y recomendación con lenguaje de hipótesis.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.llm_client import LLMClient
from ..utils.locale import get_language_instruction
from ..utils.logger import get_logger

logger = get_logger('mirofish.scenario_comparator')

SIMULATIONS_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'uploads', 'simulations'
)
REPORTS_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'uploads', 'reports'
)
COMPARISONS_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'uploads', 'comparisons'
)

COMPARE_SYSTEM_PROMPT = """\
You compare the outcomes of N social-media simulation scenarios that share
the same world and (ideally) the same agent population — only the injected
stimulus differs. Produce a decision-oriented comparative report in
Markdown with EXACTLY these sections:

1. A comparison table (one column per scenario): conversation volume,
   dominant sentiment, top objection, most receptive / most hostile
   archetype, and any contact-intent signals.
2. Key differential findings: what changed BETWEEN scenarios and what that
   suggests (hypothesis language: "en la simulación", "esto sugiere").
3. A recommendation: which scenario performed best against the stated
   requirement, with its caveats.
4. "Limitaciones y validación": synthetic population, single runs unless
   stated otherwise, and 2-4 concrete real-world checks.

Rules: facts tagged [SIM] are simulation output — never present them as
real-world facts. Never use inevitability language. Base every claim on
the provided reports/metrics; if scenarios are not comparable (different
populations), say so explicitly.
"""


def _read_json(path: str) -> Optional[Any]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _sim_summary(simulation_id: str) -> Dict[str, Any]:
    """Métricas duras + textos de un sim (robusto a archivos ausentes)."""
    sim_dir = os.path.join(SIMULATIONS_DIR, simulation_id)
    run = _read_json(os.path.join(sim_dir, 'run_state.json')) or {}
    cfg = _read_json(os.path.join(sim_dir, 'simulation_config.json')) or {}

    scenario = _read_json(os.path.join(sim_dir, 'scenario.json')) or {}
    scenario_event = (scenario.get('scenario_event') or '')[:600]

    report_md = ""
    for rid in os.listdir(REPORTS_DIR) if os.path.exists(REPORTS_DIR) else []:
        meta = _read_json(os.path.join(REPORTS_DIR, rid, 'meta.json')) or {}
        if meta.get('simulation_id') == simulation_id:
            try:
                with open(
                    os.path.join(REPORTS_DIR, rid, 'full_report.md'),
                    'r', encoding='utf-8',
                ) as f:
                    report_md = f.read()
            except Exception:
                pass

    profiles = _read_json(os.path.join(sim_dir, 'reddit_profiles.json')) or []
    return {
        "simulation_id": simulation_id,
        "scenario_event": scenario_event.strip(),
        "requirement": cfg.get('simulation_requirement', '')[:400],
        "total_actions": run.get('total_actions_count', 0),
        "twitter_actions": run.get('twitter_actions_count', 0),
        "reddit_actions": run.get('reddit_actions_count', 0),
        "rounds": run.get('total_rounds', 0),
        "population_size": len(profiles),
        "population_names_hash": hash(
            tuple(sorted(p.get('name', '') for p in profiles))
        ),
        "report_excerpt": report_md[:9000],
    }


def compare_scenarios(
    simulation_ids: List[str],
    label: Optional[str] = None,
) -> Dict[str, Any]:
    """Genera el informe comparativo y lo persiste. Devuelve metadatos."""
    if len(simulation_ids) < 2:
        raise ValueError("Se necesitan al menos 2 simulaciones para comparar")

    summaries = [_sim_summary(s) for s in simulation_ids]
    missing = [
        s["simulation_id"] for s in summaries if not s["report_excerpt"]
    ]
    if missing:
        raise ValueError(
            f"Simulaciones sin informe final: {', '.join(missing)} — "
            "genera sus informes antes de comparar"
        )

    same_population = len({s["population_names_hash"] for s in summaries}) == 1

    user_prompt_parts = [
        f"Scenarios to compare: {len(summaries)}. "
        f"Identical population across scenarios: {same_population}.\n"
    ]
    for i, s in enumerate(summaries):
        user_prompt_parts.append(
            f"\n===== ESCENARIO {i + 1} ({s['simulation_id']}) =====\n"
            f"Evento/estímulo: {s['scenario_event'] or '(no registrado)'}\n"
            f"Requisito: {s['requirement']}\n"
            f"Métricas: acciones={s['total_actions']} "
            f"(tw={s['twitter_actions']}, rd={s['reddit_actions']}), "
            f"rondas={s['rounds']}, población={s['population_size']}\n"
            f"--- INFORME (extracto) ---\n{s['report_excerpt']}\n"
        )
    user_prompt = "".join(user_prompt_parts)

    llm = LLMClient()
    content = llm.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    f"{COMPARE_SYSTEM_PROMPT}\n\n{get_language_instruction()}"
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=8000,
    )

    comparison_id = f"cmp_{uuid.uuid4().hex[:12]}"
    out_dir = os.path.join(COMPARISONS_DIR, comparison_id)
    os.makedirs(out_dir, exist_ok=True)
    meta = {
        "comparison_id": comparison_id,
        "label": label or "",
        "simulation_ids": simulation_ids,
        "same_population": same_population,
        "created_at": datetime.now().isoformat(),
        "metrics": [
            {k: v for k, v in s.items() if k != 'report_excerpt'}
            for s in summaries
        ],
    }
    with open(os.path.join(out_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(
        os.path.join(out_dir, 'comparison.md'), 'w', encoding='utf-8'
    ) as f:
        f.write(content)
    logger.info(
        f"Comparativa generada: {comparison_id} "
        f"({len(simulation_ids)} escenarios, misma población={same_population})"
    )
    meta["content"] = content
    return meta


STABILITY_SYSTEM_PROMPT = """\
You analyze K repeated runs of the SAME simulation scenario (same world,
same population, same stimulus) to measure which findings are stable.

Method:
1. Extract the discrete findings from each run's report (objections,
   sentiment patterns, archetype reactions, emergent narratives,
   contact-intent signals).
2. Match equivalent findings across runs (same substance, different
   wording = same finding).
3. Classify each finding by how many of the K runs it appears in:
   - ROBUSTO: >= 80% of runs
   - FRECUENTE: 50-79%
   - INESTABLE: < 50%

Output Markdown with: a findings table (finding | runs where it appears |
classification), a short reading of what is solid vs. noise, and a final
"Limitaciones" note reminding that stability across simulated runs is
internal consistency, NOT real-world validation. Hypothesis language only;
facts tagged [SIM] are simulation output.
"""


def analyze_stability(
    simulation_ids: List[str],
    label: Optional[str] = None,
) -> Dict[str, Any]:
    """K ejecuciones del MISMO escenario -> clasificación de estabilidad."""
    if len(simulation_ids) < 2:
        raise ValueError(
            "Se necesitan al menos 2 ejecuciones para medir estabilidad"
        )

    summaries = [_sim_summary(s) for s in simulation_ids]
    missing = [
        s["simulation_id"] for s in summaries if not s["report_excerpt"]
    ]
    if missing:
        raise ValueError(
            f"Simulaciones sin informe final: {', '.join(missing)}"
        )

    same_population = len({s["population_names_hash"] for s in summaries}) == 1
    events = {s["scenario_event"] for s in summaries}
    same_scenario = len(events) <= 1

    parts = [
        f"Repeated runs: {len(summaries)}. Same population: "
        f"{same_population}. Same stimulus: {same_scenario}.\n"
    ]
    if not same_scenario:
        parts.append(
            "WARNING: stimuli differ between runs — treat as scenario "
            "comparison, not stability analysis, and say so.\n"
        )
    for i, s in enumerate(summaries):
        parts.append(
            f"\n===== RUN {i + 1} ({s['simulation_id']}) =====\n"
            f"Métricas: acciones={s['total_actions']}, "
            f"rondas={s['rounds']}\n"
            f"--- INFORME ---\n{s['report_excerpt'][:7000]}\n"
        )

    llm = LLMClient()
    content = llm.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    f"{STABILITY_SYSTEM_PROMPT}\n\n"
                    f"{get_language_instruction()}"
                ),
            },
            {"role": "user", "content": "".join(parts)},
        ],
        temperature=0.2,
        max_tokens=8000,
    )

    comparison_id = f"stb_{uuid.uuid4().hex[:12]}"
    out_dir = os.path.join(COMPARISONS_DIR, comparison_id)
    os.makedirs(out_dir, exist_ok=True)
    meta = {
        "comparison_id": comparison_id,
        "type": "stability",
        "label": label or "",
        "simulation_ids": simulation_ids,
        "same_population": same_population,
        "same_scenario": same_scenario,
        "created_at": datetime.now().isoformat(),
        "metrics": [
            {k: v for k, v in s.items() if k != 'report_excerpt'}
            for s in summaries
        ],
    }
    with open(os.path.join(out_dir, 'meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(
        os.path.join(out_dir, 'comparison.md'), 'w', encoding='utf-8'
    ) as f:
        f.write(content)
    logger.info(
        f"Análisis de estabilidad: {comparison_id} "
        f"({len(simulation_ids)} runs, mismo estímulo={same_scenario})"
    )
    meta["content"] = content
    return meta
