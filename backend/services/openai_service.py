import os
import json
from openai import AzureOpenAI

from models.schemas import SummarizeRequest


SYSTEM_PROMPT = (
    "You are a senior HSE (Health, Safety & Environment) analyst. "
    "You MUST respond with valid JSON only — no markdown fences, no prose outside the JSON. "
    "Return exactly this structure:\n"
    '{"user_summary": "...", "manager_summary": "..."}\n\n'
    "user_summary rules:\n"
    "- Audience: HSE team / internal staff\n"
    "- Format: markdown bullet points (start each point with '• ')\n"
    "- Cover: key metrics with specific numbers, top facilities, top risk categories, "
    "positive highlights, and 2-3 recommended actions\n"
    "- Length: 200-300 words\n\n"
    "manager_summary rules:\n"
    "- Audience: VP / Manager (email-ready)\n"
    "- Format: exactly 3-5 bullet points (start each with '• ')\n"
    "- Crisp, data-driven, action-oriented\n"
    "- Length: 60-80 words total — no more"
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

Return ONLY the JSON object with user_summary and manager_summary keys."""


def generate_summary(req: SummarizeRequest) -> dict:
    """Returns {"user_summary": str, "manager_summary": str}"""
    client = _get_client()

    kwargs = dict(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(req)},
        ],
        temperature=0.3,
        max_tokens=900,
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

    return parsed
