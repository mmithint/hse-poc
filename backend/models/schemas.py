from pydantic import BaseModel
from typing import Dict, List, Optional


class ChartData(BaseModel):
    by_facility: Dict[str, int]
    by_category: Dict[str, int]
    safe_vs_atrisk: Dict[str, int]
    top_atrisk_categories: Dict[str, int]


class UploadResponse(BaseModel):
    upload_id: str
    chart_data: ChartData
    date_range: str
    total_observations: int
    atrisk_descriptions: List[str]


class SummarizeRequest(BaseModel):
    upload_id: str
    chart_data: ChartData
    date_range: str
    total_observations: int
    atrisk_descriptions: List[str]


class SummarizeResponse(BaseModel):
    user_summary: str
    manager_summary: str


class EmailRequest(BaseModel):
    to_email: str
    subject: str
    manager_summary: str
    upload_id: str


class EmailResponse(BaseModel):
    success: bool
    message: str


class DownloadReportRequest(BaseModel):
    upload_id: str
    user_summary: str
    total_observations: int


# ── History ───────────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    upload_id: str
    filename: str
    uploaded_by: str
    upload_date: str
    date_range: str
    total_observations: int
    user_summary: Optional[str] = None
    manager_summary: Optional[str] = None


class HistoryResponse(BaseModel):
    uploads: List[HistoryItem]


# ── Comparison ────────────────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    current_upload_id: str
    previous_upload_id: str


class DeltaCard(BaseModel):
    label: str
    current: float
    previous: float
    delta: float
    delta_pct: float
    good_direction: str  # "up" or "down" — tells frontend which direction is positive


class CompareResponse(BaseModel):
    current_date_range: str
    previous_date_range: str
    delta_cards: List[DeltaCard]
    current_chart_data: ChartData
    previous_chart_data: ChartData
