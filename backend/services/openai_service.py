import os
import json
from openai import AzureOpenAI

from models.schemas import SummarizeRequest


SYSTEM_PROMPT = (
    "You are a senior HSE (Health, Safety & Environment) analyst. "
    "You MUST respond with valid JSON only -- no markdown fences, no prose outside the JSON. "
    "Return exactly this structure:\n"
    '{"user_summary": "...", "manager_summary": "...", "detailed_summary": "...", '
    '"interventions_by_facility": {"FacilityA": 5, ...}, "total_interventions": 8, '
    '"category_analysis": [{"category": "...", "positive_trends": ["..."], "remaining_exposure": ["..."]}]}\n\n'

    "INTERVENTION DETECTION:\n"
    "- Analyze each observation description provided\n"
    "- An 'intervention' is when someone proactively took a safety action: stopped unsafe work, "
    "corrected a hazard, coached a worker, issued a stop-work authority, or otherwise actively "
    "intervened to prevent an incident\n"
    "- Count interventions per facility and return as interventions_by_facility dict\n"
    "- Return total_interventions as the sum of all interventions\n"
    "- If no descriptions are provided or none qualify, return empty dict and 0\n\n"

    "CATEGORY ANALYSIS:\n"
    "- Analyze the top at-risk categories from the observation data\n"
    "- For each major category (top 4-6 by observation count), return an object with:\n"
    "  - category: the category name\n"
    "  - positive_trends: list of 2-4 specific positive behaviors or safe practices observed "
    "(e.g., 'Red zone awareness', 'Proper PPE usage', 'Tool tethering compliance')\n"
    "  - remaining_exposure: list of 2-4 specific remaining risks or unsafe behaviors observed "
    "(e.g., 'Hands near pinch points', 'Standing too close to suspended loads')\n"
    "- Base these on actual observation descriptions, not generic safety items\n"
    "- Return as category_analysis array\n\n"

    "user_summary rules:\n"
    "- Audience: HSE team / internal staff\n"
    "- Format: markdown bullet points (start each point with '\u2022 ')\n"
    "- Cover: key metrics with specific numbers, top facilities, top risk categories, "
    "positive highlights, and 2-3 recommended actions\n"
    "- Length: 200-300 words\n\n"

    "manager_summary rules:\n"
    "- Audience: VP / Manager (email-ready)\n"
    "- Format: exactly 3-5 bullet points (start each with '\u2022 ')\n"
    "- Crisp, data-driven, action-oriented\n"
    "- Length: 60-80 words total -- no more\n\n"

    "detailed_summary rules:\n"
    "- Audience: HSE Director (Steven)\n"
    "- Format: structured sections with ## headers (markdown)\n"
    "- Sections: Weekly Overview, Facility-Specific Insights, Intervention Analysis, "
    "Category Breakdown, At-Risk Patterns, Actionable Recommendations\n"
    "- Include specific numbers, percentages, and facility names\n"
    "- Length: 500-700 words"
)


def _get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )


def _build_prompt(req: SummarizeRequest) -> str:
    by_facility = "\n".join(f"  - {k}: {v}" for k, v in req.chart_data.by_facility.items())
    by_category = "\n".join(f"  - {k}: {v}" for k, v in req.chart_data.by_category.items())
    top_atrisk = "\n".join(
        f"  - {k}: {v}" for k, v in req.chart_data.top_atrisk_categories.items()
    )
    atrisk_sample = "\n".join(f"  - {d}" for d in req.atrisk_descriptions[:10])

    safe = req.chart_data.safe_vs_atrisk.get("Safe", 0)
    atrisk = req.chart_data.safe_vs_atrisk.get("At Risk", 0)
    total = req.total_observations
    atrisk_pct = round((atrisk / total * 100), 1) if total else 0

    # Include observation details for intervention detection (limit to 500)
    obs_lines = []
    for obs in req.observation_details[:500]:
        desc = obs.get("description", "")[:300]
        facility = obs.get("facility", "Unknown")
        obs_lines.append(f"  - [{facility}] {desc}")
    obs_section = "\n".join(obs_lines) if obs_lines else "  (no descriptions provided)"

    return f"""Generate the HSE summary JSON for period: {req.date_range}

OBSERVATION DATA:
- Total: {total}  |  Safe: {safe}  |  At-Risk: {atrisk} ({atrisk_pct}%)

BY FACILITY:
{by_facility}

BY CATEGORY:
{by_category}

TOP AT-RISK CATEGORIES:
{top_atrisk}

SAMPLE AT-RISK DESCRIPTIONS:
{atrisk_sample}

ALL OBSERVATION DESCRIPTIONS (for intervention detection):
{obs_section}

Return ONLY the JSON object with user_summary, manager_summary, detailed_summary, interventions_by_facility, total_interventions, and category_analysis keys."""


def generate_summary(req: SummarizeRequest) -> dict:
    """Returns {"user_summary": str, "manager_summary": str, "detailed_summary": str,
                "interventions_by_facility": dict, "total_interventions": int}"""
    client = _get_client()

    kwargs = dict(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(req)},
        ],
        max_completion_tokens=3000,
    )

    # JSON mode requires api_version >= 2024-02-01
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "")
    if api_version >= "2024-02-01":
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present (fallback for older API versions)
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI returned invalid JSON: {exc}\nRaw output: {raw[:300]}")

    if "user_summary" not in parsed or "manager_summary" not in parsed:
        raise ValueError(
            f"AI JSON missing required keys. Got: {list(parsed.keys())}"
        )

    # Ensure defaults for new fields
    parsed.setdefault("detailed_summary", "")
    parsed.setdefault("interventions_by_facility", {})
    parsed.setdefault("total_interventions", 0)
    parsed.setdefault("category_analysis", [])

    return parsed


def generate_cross_week_narrative(weeks_analyses: list[dict]) -> dict:
    """Generate a cross-week evolution narrative from saved per-week category analyses.

    Each entry in weeks_analyses should have:
      - date_range, total_observations, safe_pct, atrisk_pct, total_interventions
      - category_analysis (list of per-category dicts from the per-week AI call)
    """
    client = _get_client()

    system = (
        "You are a senior HSE analyst. Given per-week category analyses and KPI data, "
        "produce a cross-week evolution narrative. "
        "You MUST respond with valid JSON only -- no markdown fences, no prose outside the JSON. "
        "Return exactly this structure:\n"
        '{"overall_narrative": "2-3 sentences on how safety evolved across the weeks...", '
        '"improvements": ["Specific improvement 1", "Specific improvement 2"], '
        '"persistent_risks": ["Persistent risk 1", "Persistent risk 2"]}\n\n'
        "Rules:\n"
        "- overall_narrative: 2-3 sentences summarizing the safety trajectory across all weeks\n"
        "- improvements: 3-5 specific positive trends that improved from earlier to later weeks\n"
        "- persistent_risks: 3-5 specific risks that remained or worsened across weeks\n"
        "- Be concrete and reference specific categories and behaviors, not generic statements"
    )

    user_msg = "Analyze the cross-week evolution from these weekly analyses:\n\n"
    for i, w in enumerate(weeks_analyses, 1):
        user_msg += f"WEEK {i} ({w['date_range']}):\n"
        user_msg += f"  Total Observations: {w['total_observations']}\n"
        user_msg += f"  Safe %: {w['safe_pct']} | At-Risk %: {w['atrisk_pct']}\n"
        user_msg += f"  Interventions: {w['total_interventions']}\n"
        ca = w.get("category_analysis", [])
        if ca:
            user_msg += "  Category Analysis:\n"
            for cat in ca:
                user_msg += f"    - {cat.get('category', 'Unknown')}:\n"
                user_msg += f"      Positives: {', '.join(cat.get('positive_trends', []))}\n"
                user_msg += f"      Risks: {', '.join(cat.get('remaining_exposure', []))}\n"
        user_msg += "\n"

    user_msg += "Return ONLY the JSON object with overall_narrative, improvements, and persistent_risks."

    kwargs = dict(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        max_completion_tokens=1500,
    )

    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "")
    if api_version >= "2024-02-01":
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    parsed = json.loads(raw)
    parsed.setdefault("overall_narrative", "")
    parsed.setdefault("improvements", [])
    parsed.setdefault("persistent_risks", [])
    return parsed
