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
    summary: str


class EmailRequest(BaseModel):
    to_email: str
    subject: str
    summary: str
    upload_id: str


class EmailResponse(BaseModel):
    success: bool
    message: str


class DownloadReportRequest(BaseModel):
    upload_id: str
    summary: str
    total_observations: int
