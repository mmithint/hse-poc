import os
import json
import asyncio
import logging
from typing import List, Dict

from openai import AzureOpenAI

from models.schemas import SummarizeRequest

logger = logging.getLogger(__name__)

# -- Batch config --------------------------------------------------------------
INTERVENTION_BATCH_SIZE = 200
MAX_CONCURRENT_BATCHES = 10

# -- System prompts (one per pipeline) ----------------------------------------

SUMMARY_SYSTEM_PROMPT = (
    "You are a senior HSE (Health, Safety & Environment) analyst. "
    "You MUST respond with valid JSON only -- no markdown fences, no prose outside the JSON. "
    "Return exactly this structure:\n"
    '{"user_summary": "...", "manager_summary": "...", "detailed_summary": "..."}\n\n'
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

INTERVENTION_SYSTEM_PROMPT = (
    "You are a senior HSE analyst specializing in intervention detection. "
    "You MUST respond with valid JSON only -- no markdown fences, no prose outside the JSON. "
    "Return exactly this structure:\n"
    '{"interventions": [{"facility": "FacilityName", "snippet": "brief reason"}]}\n\n'
    "Rules:\n"
    "- Analyze each observation description provided\n"
    "- An 'intervention' is when someone proactively took a safety action: stopped unsafe work, "
    "corrected a hazard, coached a worker, issued a stop-work authority, or otherwise actively "
    "intervened to prevent an incident\n"
    "- For each description that qualifies as an intervention, add one entry with the facility "
    "and a brief snippet (10 words max) explaining why it qualifies\n"
    "- If no descriptions qualify, return {\"interventions\": []}\n"
    "- Be strict: routine observations without active intervention do NOT count"
)

CATEGORY_SYSTEM_PROMPT = (
    "You are a senior HSE analyst specializing in category trend analysis. "
    "You MUST respond with valid JSON only -- no markdown fences, no prose outside the JSON. "
    "Return exactly this structure:\n"
    '{"category_analysis": [{"category": "...", "positive_trends": ["..."], "remaining_exposure": ["..."]}]}\n\n'
    "Rules:\n"
    "- Analyze the top at-risk categories from the observation data\n"
    "- For each major category (top 4-6 by observation count), return an object with:\n"
    "  - category: the category name\n"
    "  - positive_trends: list of 2-4 specific positive behaviors or safe practices observed "
    "(e.g., 'Red zone awareness', 'Proper PPE usage', 'Tool tethering compliance')\n"
    "  - remaining_exposure: list of 2-4 specific remaining risks or unsafe behaviors observed "
    "(e.g., 'Hands near pinch points', 'Standing too close to suspended loads')\n"
    "- Base these on actual observation descriptions, not generic safety items\n"
    "- Return as category_analysis array"
)


# -- Azure OpenAI helpers -----------------------------------------------------

def _get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )


def _call_llm_sync(system: str, user: str, max_tokens: int = 2000) -> dict:
    """Synchronous LLM call — returns parsed JSON dict."""
    client = _get_client()
    kwargs = dict(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_completion_tokens=max_tokens,
    )
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "")
    if api_version >= "2024-02-01":
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


async def _call_llm(system: str, user: str, max_tokens: int = 2000) -> dict:
    """Async wrapper around the synchronous OpenAI SDK."""
    return await asyncio.to_thread(_call_llm_sync, system, user, max_tokens)


# -- Pipeline 1: Summaries (1 call) -------------------------------------------

def _build_summary_prompt(req: SummarizeRequest) -> str:
    by_facility = "\n".join(f"  - {k}: {v}" for k, v in req.chart_data.by_facility.items())
    by_category = "\n".join(f"  - {k}: {v}" for k, v in req.chart_data.by_category.items())
    top_atrisk = "\n".join(
        f"  - {k}: {v}" for k, v in req.chart_data.top_atrisk_categories.items()
    )
    atrisk_sample = "\n".join(f"  - {d}" for d in req.atrisk_descriptions[:20])

    safe = req.chart_data.safe_vs_atrisk.get("Safe", 0)
    atrisk = req.chart_data.safe_vs_atrisk.get("At Risk", 0)
    total = req.total_observations
    atrisk_pct = round((atrisk / total * 100), 1) if total else 0

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

Return ONLY the JSON object with user_summary, manager_summary, and detailed_summary keys."""


async def _generate_summaries(req: SummarizeRequest) -> dict:
    """Pipeline 1: Generate all three text summaries in a single LLM call."""
    parsed = await _call_llm(
        SUMMARY_SYSTEM_PROMPT,
        _build_summary_prompt(req),
        max_tokens=2500,
    )
    if "user_summary" not in parsed or "manager_summary" not in parsed:
        raise ValueError(f"AI JSON missing required keys. Got: {list(parsed.keys())}")
    parsed.setdefault("detailed_summary", "")
    return {
        "user_summary": parsed["user_summary"],
        "manager_summary": parsed["manager_summary"],
        "detailed_summary": parsed["detailed_summary"],
    }


# -- Pipeline 2: Interventions (N batches) ------------------------------------

async def _detect_interventions_batch(
    batch: List[Dict[str, str]],
    semaphore: asyncio.Semaphore,
) -> List[dict]:
    """Process one batch of observation descriptions for intervention detection."""
    obs_lines = []
    for obs in batch:
        desc = obs.get("description", "")
        facility = obs.get("facility", "Unknown")
        obs_lines.append(f"  - [{facility}] {desc}")
    obs_section = "\n".join(obs_lines)

    prompt = f"""Analyze these {len(batch)} observation descriptions for safety interventions:

{obs_section}

Return ONLY the JSON object with an "interventions" array."""

    async with semaphore:
        try:
            parsed = await _call_llm(
                INTERVENTION_SYSTEM_PROMPT,
                prompt,
                max_tokens=1500,
            )
            return parsed.get("interventions", [])
        except Exception as exc:
            logger.warning("Intervention batch failed: %s", exc)
            return []


async def _detect_interventions_batched(
    observation_details: List[Dict[str, str]],
) -> dict:
    """Pipeline 2: Batch all observations and detect interventions in parallel."""
    if not observation_details:
        return {"interventions_by_facility": {}, "total_interventions": 0}

    # Split into batches
    batches = [
        observation_details[i : i + INTERVENTION_BATCH_SIZE]
        for i in range(0, len(observation_details), INTERVENTION_BATCH_SIZE)
    ]
    logger.info(
        "Intervention detection: %d observations in %d batches",
        len(observation_details), len(batches),
    )

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)
    tasks = [_detect_interventions_batch(batch, semaphore) for batch in batches]
    results = await asyncio.gather(*tasks)

    # Merge: count interventions per facility across all batches
    facility_counts: Dict[str, int] = {}
    for batch_interventions in results:
        for item in batch_interventions:
            facility = item.get("facility", "Unknown")
            facility_counts[facility] = facility_counts.get(facility, 0) + 1

    total = sum(facility_counts.values())
    # Sort descending by count
    sorted_counts = dict(sorted(facility_counts.items(), key=lambda x: x[1], reverse=True))

    return {
        "interventions_by_facility": sorted_counts,
        "total_interventions": total,
    }


# -- Pipeline 3: Category Analysis (1 call) -----------------------------------

def _build_category_prompt(req: SummarizeRequest, observation_details: list) -> str:
    by_category = "\n".join(f"  - {k}: {v}" for k, v in req.chart_data.by_category.items())
    top_atrisk = "\n".join(
        f"  - {k}: {v}" for k, v in req.chart_data.top_atrisk_categories.items()
    )

    safe = req.chart_data.safe_vs_atrisk.get("Safe", 0)
    atrisk = req.chart_data.safe_vs_atrisk.get("At Risk", 0)
    total = req.total_observations
    atrisk_pct = round((atrisk / total * 100), 1) if total else 0

    # Sample up to 50 at-risk descriptions with their categories
    atrisk_details = [
        obs for obs in observation_details
        if obs.get("category", "") in req.chart_data.top_atrisk_categories
    ][:50]
    samples = "\n".join(
        f"  - [{obs.get('category', 'Unknown')}] {obs.get('description', '')}"
        for obs in atrisk_details
    )
    if not samples:
        samples = "\n".join(f"  - {d}" for d in req.atrisk_descriptions[:30])

    return f"""Analyze category trends for period: {req.date_range}

OBSERVATION DATA:
- Total: {total}  |  Safe: {safe}  |  At-Risk: {atrisk} ({atrisk_pct}%)

BY CATEGORY:
{by_category}

TOP AT-RISK CATEGORIES:
{top_atrisk}

SAMPLE AT-RISK OBSERVATION DESCRIPTIONS (with categories):
{samples}

Return ONLY the JSON object with a "category_analysis" array."""


async def _generate_category_analysis(
    req: SummarizeRequest,
    observation_details: list,
) -> dict:
    """Pipeline 3: Generate per-category positive trends and remaining exposures."""
    parsed = await _call_llm(
        CATEGORY_SYSTEM_PROMPT,
        _build_category_prompt(req, observation_details),
        max_tokens=1500,
    )
    return {"category_analysis": parsed.get("category_analysis", [])}


# -- Orchestrator --------------------------------------------------------------

async def generate_summary(
    req: SummarizeRequest,
    observation_details: List[Dict[str, str]] = None,
) -> dict:
    """
    Run three LLM pipelines in parallel:
      1. Summaries (1 call)
      2. Intervention detection (N batched calls)
      3. Category analysis (1 call)
    Returns merged dict with all keys.
    """
    if observation_details is None:
        observation_details = req.observation_details or []

    summaries_task = _generate_summaries(req)
    interventions_task = _detect_interventions_batched(observation_details)
    category_task = _generate_category_analysis(req, observation_details)

    summaries, interventions, categories = await asyncio.gather(
        summaries_task,
        interventions_task,
        category_task,
    )

    return {**summaries, **interventions, **categories}


# -- Cross-week narrative (unchanged) -----------------------------------------

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
