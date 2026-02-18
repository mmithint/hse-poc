import os
from openai import AzureOpenAI

from models.schemas import SummarizeRequest


SYSTEM_PROMPT = (
    "You are a senior HSE (Health, Safety & Environment) analyst preparing an "
    "executive summary for a Vice President. Your summaries are:\n"
    "- Concise but comprehensive (250-350 words)\n"
    "- Data-driven with specific numbers\n"
    "- Action-oriented with clear recommendations\n"
    "- Professional in tone, avoiding jargon\n"
    "- Structured with the four sections requested"
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

    return f"""Please generate a VP-level HSE Observation Summary for the period: {req.date_range}

OBSERVATION DATA:
- Total Observations: {req.total_observations}
- Safe Observations: {safe}
- At-Risk Observations: {atrisk}

OBSERVATIONS BY FACILITY:
{by_facility}

OBSERVATIONS BY CATEGORY:
{by_category}

TOP AT-RISK CATEGORIES:
{top_atrisk}

SAMPLE AT-RISK OBSERVATION DESCRIPTIONS:
{atrisk_sample}

Please structure your summary with exactly these four sections:
1. Executive Overview (2-3 sentences with key metrics)
2. Leading Indicators / Positive Performance
3. Areas of Concern (reference specific at-risk categories and descriptions)
4. Recommended Actions (3-4 specific, actionable items)

Use the actual numbers from the data. Reference specific facilities and categories by name."""


def generate_summary(req: SummarizeRequest) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(req)},
        ],
        temperature=0.3,
        max_tokens=700,
    )
    return response.choices[0].message.content
