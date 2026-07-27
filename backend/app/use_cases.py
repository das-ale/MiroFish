"""Plantillas de caso de uso ("productos-pregunta").

Convierten el lienzo libre (documentos + requisito) en flujos guiados que
responden UNA pregunta de negocio con veredicto accionable:
- price_test:  ¿cómo recibirá el mercado este producto/servicio a precio X?
- ad_test:     ¿funcionará este anuncio con esta audiencia?
- launch_test: ¿cómo reaccionará el mercado a este lanzamiento/comunicado?

Cada plantilla parametriza: el formulario (form_fields, consumido por el
wizard del frontend), el simulation_requirement generado, y el outline fijo
del informe que termina en VEREDICTO antes de Limitaciones. use_case=None
mantiene el flujo libre original intacto.
"""

from typing import Any, Dict, List, Optional

# Instrucción compartida: el estímulo debe publicarse literal
_VERBATIM_RULE = (
    "El post inicial de la simulación debe contener el TEXTO EXACTO del "
    "estímulo (sin parafrasear, sin resumir, sin traducir) publicado por la "
    "cuenta oficial de la marca/anunciante."
)

_COMMON_OUTLINE_TAIL = [
    {
        "title": "Hipótesis comprobables",
        "description": "Hipótesis accionables derivadas de la simulación, formuladas para poder validarse en la realidad.",
    },
    {
        "title": "Veredicto",
        "description": "Scorecard final que responde LA pregunta del test.",
    },
    {
        "title": "Limitaciones y validación",
        "description": "Supuestos, población sintética, y 2-4 comprobaciones concretas en el mundo real.",
    },
]

_VERDICT_BASE = (
    "La sección «Veredicto» es OBLIGATORIA y debe contener exactamente: "
    "(1) Recepción esperada en una frase (cualitativa, sin porcentajes "
    "falsos); (2) Top 3 objeciones/fricciones observadas, por orden de "
    "peso en la simulación; (3) Segmentos favorables y contrarios; "
    "(4) Recomendación final en negrita: **GO**, **NO-GO** o **AJUSTAR**, "
    "con las condiciones o cambios concretos que la justifican. "
    "El veredicto responde la pregunta del test, no divaga."
)

USE_CASES: Dict[str, Dict[str, Any]] = {
    "price_test": {
        "name": {"es": "Test de Precio", "en": "Price Test", "zh": "定价测试"},
        "description": {
            "es": "¿Cómo recibirá el mercado este producto o servicio a este precio?",
            "en": "How will the market receive this product or service at this price?",
            "zh": "市场将如何接受这个价格的产品或服务？",
        },
        "form_fields": [
            {"key": "product", "label": {"es": "Producto/servicio", "en": "Product/service", "zh": "产品/服务"}, "type": "text", "required": True},
            {"key": "price", "label": {"es": "Precio y condiciones (permanencia, setup...)", "en": "Price and terms", "zh": "价格与条款"}, "type": "text", "required": True},
            {"key": "value_prop", "label": {"es": "Propuesta de valor (qué incluye, por qué ese precio)", "en": "Value proposition", "zh": "价值主张"}, "type": "textarea", "required": True},
            {"key": "audience", "label": {"es": "Audiencia objetivo (quién compra, dónde)", "en": "Target audience", "zh": "目标受众"}, "type": "textarea", "required": True},
            {"key": "competitors", "label": {"es": "Competencia y precios de referencia (opcional)", "en": "Competitors and reference prices (optional)", "zh": "竞争对手与参考价格（可选）"}, "type": "textarea", "required": False},
        ],
        "requirement_template": (
            "TEST DE PRECIO. Producto/servicio: {product}. Precio y "
            "condiciones a testear: {price}. Propuesta de valor: "
            "{value_prop}. Audiencia objetivo: {audience}. "
            "Competencia/referencias: {competitors}.\n"
            "Simula la conversación pública de la audiencia al conocer el "
            "precio: reacciones por segmento, comparaciones con "
            "alternativas, objeciones al precio y a las condiciones, "
            "disposición a pagar y señales de intención de compra. "
            + _VERBATIM_RULE
        ),
        "scenario_event_template": (
            "La marca anuncia públicamente: {product} a {price}. "
            "Detalle de la oferta: {value_prop}"
        ),
        "report_outline": [
            {"title": "Recepción del precio", "description": "Cómo aterrizó el precio en la conversación simulada: primera reacción global y evolución."},
            {"title": "Objeciones y sensibilidad al precio", "description": "Objeciones concretas al precio/condiciones y qué segmentos las expresan."},
            {"title": "Segmentos: quién compra y quién se descarta", "description": "Reacción por arquetipo: favorables, contrarios, condicionales; comparaciones con alternativas."},
        ] + _COMMON_OUTLINE_TAIL,
        "verdict_prompt": _VERDICT_BASE + (
            " Para el test de precio, la recomendación AJUSTAR debe "
            "concretar dirección (subir/bajar/reestructurar) y qué "
            "condición (permanencia, setup, garantía) genera más fricción."
        ),
    },
    "ad_test": {
        "name": {"es": "Test de Anuncio", "en": "Ad Test", "zh": "广告测试"},
        "description": {
            "es": "¿Funcionará este anuncio (copy + creativo) con esta audiencia?",
            "en": "Will this ad (copy + creative) work with this audience?",
            "zh": "这个广告对这个受众有效吗？",
        },
        "form_fields": [
            {"key": "brand", "label": {"es": "Marca/anunciante", "en": "Brand/advertiser", "zh": "品牌/广告主"}, "type": "text", "required": True},
            {"key": "headline", "label": {"es": "Titular del anuncio", "en": "Ad headline", "zh": "广告标题"}, "type": "text", "required": True},
            {"key": "copy", "label": {"es": "Copy COMPLETO del anuncio (texto literal)", "en": "FULL ad copy (verbatim)", "zh": "广告完整文案（原文）"}, "type": "textarea", "required": True},
            {"key": "creative_description", "label": {"es": "Descripción del creativo (qué se ve: imagen/vídeo, estilo, texto sobre imagen)", "en": "Creative description (what is shown)", "zh": "创意素材描述"}, "type": "textarea", "required": True},
            {"key": "cta_offer", "label": {"es": "CTA y oferta (botón, promoción, landing)", "en": "CTA and offer", "zh": "CTA与优惠"}, "type": "text", "required": True},
            {"key": "audience", "label": {"es": "Audiencia objetivo del anuncio (segmentación)", "en": "Ad target audience", "zh": "广告目标受众"}, "type": "textarea", "required": True},
        ],
        "requirement_template": (
            "TEST DE ANUNCIO (Meta Ads o similar). Anunciante: {brand}. "
            "Titular: «{headline}». Copy literal del anuncio: «{copy}». "
            "Creativo (descripción): {creative_description}. CTA/oferta: "
            "{cta_offer}. Audiencia objetivo: {audience}.\n"
            "Simula la reacción de la audiencia al ver el anuncio en su "
            "feed: comentarios, interpretaciones y malinterpretaciones del "
            "mensaje, objeciones a la oferta, señales de interés o rechazo, "
            "y riesgo de comentarios negativos visibles. " + _VERBATIM_RULE
            + " El anuncio se publica como post de la cuenta de {brand} "
            "con el titular y el copy EXACTOS."
        ),
        "scenario_event_template": (
            "{brand} publica un anuncio: «{headline}» — {copy} "
            "[Creativo: {creative_description}] CTA: {cta_offer}"
        ),
        "report_outline": [
            {"title": "Reacción al anuncio", "description": "Primera reacción de la audiencia simulada: atención, tono de los comentarios, qué parte del mensaje domina."},
            {"title": "Interpretaciones y malentendidos del mensaje", "description": "Cómo se entendió (y malentendió) el titular, el copy y la oferta; ángulos que no aterrizaron."},
            {"title": "Reacción por segmento y riesgo de comentarios", "description": "Qué arquetipos responden mejor/peor y qué comentarios negativos visibles podrían aparecer bajo el anuncio."},
        ] + _COMMON_OUTLINE_TAIL,
        "verdict_prompt": _VERDICT_BASE + (
            " Para el test de anuncio, AJUSTAR debe proponer cambios "
            "concretos de titular/copy/oferta. En Limitaciones debe constar "
            "obligatoriamente: los agentes reaccionan al mensaje, la oferta "
            "y el ángulo a partir de una descripción textual del creativo — "
            "NO se testea el impacto visual real (thumb-stop, estética, "
            "calidad de producción)."
        ),
    },
    "launch_test": {
        "name": {"es": "Test de Lanzamiento", "en": "Launch Test", "zh": "发布测试"},
        "description": {
            "es": "¿Cómo reaccionará el mercado a este lanzamiento, campaña o comunicado?",
            "en": "How will the market react to this launch, campaign or announcement?",
            "zh": "市场将如何回应这次发布？",
        },
        "form_fields": [
            {"key": "brand", "label": {"es": "Marca/organización", "en": "Brand/organization", "zh": "品牌/组织"}, "type": "text", "required": True},
            {"key": "launch", "label": {"es": "Qué se lanza (producto, campaña, apertura, comunicado)", "en": "What is being launched", "zh": "发布内容"}, "type": "textarea", "required": True},
            {"key": "message", "label": {"es": "Mensaje/comunicado EXACTO del lanzamiento", "en": "EXACT launch message", "zh": "发布原文"}, "type": "textarea", "required": True},
            {"key": "channel_date", "label": {"es": "Canal y momento (dónde y cuándo se anuncia)", "en": "Channel and timing", "zh": "渠道与时机"}, "type": "text", "required": True},
            {"key": "audience", "label": {"es": "Mercado/audiencia y contexto competitivo", "en": "Market/audience and competitive context", "zh": "市场/受众与竞争背景"}, "type": "textarea", "required": True},
        ],
        "requirement_template": (
            "TEST DE LANZAMIENTO. Marca: {brand}. Lanzamiento: {launch}. "
            "Comunicado literal: «{message}». Canal y momento: "
            "{channel_date}. Mercado/audiencia: {audience}.\n"
            "Simula la conversación pública tras el anuncio: narrativas que "
            "emergen, quién amplifica a favor y en contra, cronología de la "
            "reacción, preguntas y dudas que surgen, y riesgos "
            "reputacionales. " + _VERBATIM_RULE
        ),
        "scenario_event_template": (
            "{brand} anuncia en {channel_date}: {message}"
        ),
        "report_outline": [
            {"title": "Cronología de la reacción", "description": "Cómo evolucionó la conversación simulada desde el anuncio: fases, picos y giros."},
            {"title": "Narrativas emergentes: aliados y detractores", "description": "Qué narrativas se formaron, quién las empuja y cuáles ganaron tracción."},
            {"title": "Preguntas, dudas y riesgos reputacionales", "description": "Qué preguntó la audiencia, qué quedó sin responder y qué riesgos asomaron."},
        ] + _COMMON_OUTLINE_TAIL,
        "verdict_prompt": _VERDICT_BASE + (
            " Para el test de lanzamiento, AJUSTAR debe incluir un plan de "
            "respuesta: qué pregunta/objeción hay que tener contestada "
            "ANTES de lanzar y qué narrativa conviene reforzar."
        ),
    },
}


def get_use_case(use_case_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not use_case_id:
        return None
    return USE_CASES.get(use_case_id)


def list_use_cases() -> List[Dict[str, Any]]:
    """Listado para el wizard del frontend (sin prompts internos)."""
    return [
        {
            "id": uid,
            "name": uc["name"],
            "description": uc["description"],
            "form_fields": uc["form_fields"],
        }
        for uid, uc in USE_CASES.items()
    ]


def render_requirement(use_case_id: str, inputs: Dict[str, Any]) -> str:
    """simulation_requirement desde la plantilla + inputs del formulario."""
    uc = USE_CASES[use_case_id]
    values = _fill_defaults(uc, inputs)
    return uc["requirement_template"].format(**values)


def render_scenario_event(use_case_id: str, inputs: Dict[str, Any]) -> str:
    uc = USE_CASES[use_case_id]
    values = _fill_defaults(uc, inputs)
    return uc["scenario_event_template"].format(**values)


def get_report_instructions(use_case_id: Optional[str]) -> Optional[str]:
    """Instrucciones de outline fijo + veredicto para el ReportAgent."""
    uc = get_use_case(use_case_id)
    if not uc:
        return None
    outline_lines = "\n".join(
        f"{i + 1}. «{s['title']}»: {s['description']}"
        for i, s in enumerate(uc["report_outline"])
    )
    return (
        "ESTE INFORME ES UN "
        f"{uc['name'].get('es', use_case_id).upper()} con estructura "
        "OBLIGATORIA. El outline debe tener EXACTAMENTE estas secciones, "
        "en este orden y con estos títulos (traducidos al idioma del "
        f"informe):\n{outline_lines}\n\n{uc['verdict_prompt']}"
    )


def _fill_defaults(uc: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for field in uc["form_fields"]:
        raw = inputs.get(field["key"], "")
        values[field["key"]] = str(raw).strip() if raw else "(no especificado)"
    return values
