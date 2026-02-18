import io
import uuid
import pandas as pd
from typing import Tuple

from models.schemas import ChartData, UploadResponse

# Map Excel column headers to internal field names
COLUMN_MAP = {
    "Observation Date": "observation_date",
    "Facility": "facility",
    "Description": "description",
    "Observation Catergory": "category",   # matches the typo in the sample data
    "Observation Category": "category",
    "Type of observation": "observation_type",
    "Stop work authority": "stop_work_authority",
    "Corrective Actions Taken": "corrective_actions",
}


def parse_excel(file_bytes: bytes) -> Tuple[str, UploadResponse]:
    """
    Parse Excel bytes, aggregate data, and return (upload_id, UploadResponse).
    """
    df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")

    # Normalize column names — strip whitespace first, then rename
    df.columns = df.columns.str.strip()
    df.rename(columns=COLUMN_MAP, inplace=True)

    # Drop fully empty rows
    df.dropna(how="all", inplace=True)

    # Normalize observation type: "at risk" / "AT RISK" / "Safe" / "safe" → title case
    df["observation_type"] = (
        df["observation_type"].astype(str).str.strip().str.title()
    )

    # Normalize category and facility — strip whitespace
    for col in ("facility", "category"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # --- Aggregations ---
    by_facility = (
        df.groupby("facility").size().sort_values(ascending=False).to_dict()
    )

    by_category = (
        df.groupby("category").size().sort_values(ascending=False).to_dict()
    )

    safe_vs_atrisk = df.groupby("observation_type").size().to_dict()
    safe_vs_atrisk.setdefault("Safe", 0)
    safe_vs_atrisk.setdefault("At Risk", 0)

    atrisk_df = df[df["observation_type"] == "At Risk"]
    top_atrisk_categories = (
        atrisk_df.groupby("category").size().sort_values(ascending=False).to_dict()
    )

    # Date range
    date_series = pd.to_datetime(df.get("observation_date", pd.Series()), errors="coerce")
    date_range = _build_date_range(date_series)

    # Sample at-risk descriptions for AI prompt (up to 10)
    atrisk_descriptions: list[str] = []
    if "description" in atrisk_df.columns:
        atrisk_descriptions = (
            atrisk_df["description"].dropna().astype(str).head(10).tolist()
        )

    upload_id = str(uuid.uuid4())
    chart_data = ChartData(
        by_facility=by_facility,
        by_category=by_category,
        safe_vs_atrisk=safe_vs_atrisk,
        top_atrisk_categories=top_atrisk_categories,
    )

    response = UploadResponse(
        upload_id=upload_id,
        chart_data=chart_data,
        date_range=date_range,
        total_observations=len(df),
        atrisk_descriptions=atrisk_descriptions,
    )
    return upload_id, response


def _build_date_range(date_series: pd.Series) -> str:
    valid = date_series.dropna()
    if valid.empty:
        return "Unknown Period"
    min_d = valid.min().strftime("%b %Y")
    max_d = valid.max().strftime("%b %Y")
    return f"{min_d} \u2013 {max_d}" if min_d != max_d else min_d
