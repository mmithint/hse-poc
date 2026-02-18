import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import io

load_dotenv()

from models.schemas import (
    UploadResponse,
    SummarizeRequest,
    SummarizeResponse,
    EmailRequest,
    EmailResponse,
    DownloadReportRequest,
)
from services.excel_service import parse_excel
from services.openai_service import generate_summary
from services.chart_service import generate_all_charts
from services.email_service import send_email
from services.pdf_service import generate_pdf

app = FastAPI(title="HSE Observation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: upload_id → { chart_data, date_range }
_sessions: dict = {}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx or .xls) are accepted.",
        )

    contents = await file.read()

    try:
        upload_id, response = parse_excel(contents)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Excel parsing failed: {exc}",
        )

    _sessions[upload_id] = {
        "chart_data": response.chart_data,
        "date_range": response.date_range,
    }

    return response


@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest):
    try:
        text = generate_summary(req)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Azure OpenAI call failed: {exc}",
        )
    return SummarizeResponse(summary=text)


@app.post("/api/send-email", response_model=EmailResponse)
async def send_email_endpoint(req: EmailRequest):
    session = _sessions.get(req.upload_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Upload session not found. Please re-upload the file.",
        )

    try:
        chart_images = generate_all_charts(session["chart_data"])
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Chart generation failed: {exc}",
        )

    try:
        send_email(
            to_email=req.to_email,
            subject=req.subject,
            summary=req.summary,
            date_range=session["date_range"],
            chart_images=chart_images,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Email sending failed: {exc}",
        )

    return EmailResponse(success=True, message=f"Report sent to {req.to_email}")


@app.post("/api/download-report")
async def download_report(req: DownloadReportRequest):
    session = _sessions.get(req.upload_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Upload session not found. Please re-upload the file.",
        )

    try:
        pdf_bytes = generate_pdf(
            chart_data=session["chart_data"],
            summary=req.summary,
            date_range=session["date_range"],
            total_observations=req.total_observations,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {exc}",
        )

    filename = f"HSE_Report_{session['date_range'].replace(' ', '_').replace('–', '-')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
