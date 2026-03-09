import os
import io
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

from db import get_client, close_client
from models.schemas import (
    UploadResponse,
    SummarizeRequest,
    SummarizeResponse,
    EmailRequest,
    EmailResponse,
    DownloadReportRequest,
    DownloadComparisonRequest,
    HistoryResponse,
    HistoryItem,
    CompareRequest,
    CompareResponse,
    DeltaCard,
    ChartData,
    MultiCompareRequest,
    MultiCompareResponse,
    WeekData,
)
from services.excel_service import parse_excel
from services.openai_service import generate_summary, generate_cross_week_narrative
from services.chart_service import generate_all_charts
from services.email_service import send_email
from services.pdf_service import generate_pdf, generate_comparison_pdf
from services.mongo_service import (
    save_upload,
    update_summaries,
    get_all_uploads,
    get_upload_by_id,
    delete_upload as mongo_delete_upload,
)

# In-memory session store kept as fast fallback for active sessions
_sessions: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = get_client()
    try:
        await client.admin.command("ping")
    except Exception as exc:
        raise RuntimeError(f"Cannot connect to MongoDB: {exc}")
    yield
    await close_client()


app = FastAPI(title="HSE Observation API", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    uploaded_by: str = Form(default="Unknown"),
):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx or .xls) are accepted.",
        )

    contents = await file.read()

    try:
        upload_id, response = parse_excel(contents)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Excel parsing failed: {exc}")

    # Keep in-memory for fast PDF/email access during the session
    _sessions[upload_id] = {
        "chart_data": response.chart_data,
        "date_range": response.date_range,
        "filename": file.filename,
    }

    # Persist to MongoDB (summaries added later by /api/summarize)
    doc = {
        "_id": upload_id,
        "filename": file.filename,
        "uploaded_by": uploaded_by.strip() or "Unknown",
        "upload_date": datetime.now(timezone.utc).isoformat(),
        "date_range": response.date_range,
        "total_observations": response.total_observations,
        "chart_data": response.chart_data.model_dump(),
        "atrisk_descriptions": response.atrisk_descriptions,
        "observation_details": response.observation_details,
        "user_summary": None,
        "manager_summary": None,
        "detailed_summary": None,
    }
    await save_upload(doc)

    return response


@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest):
    try:
        # Fetch full observation_details from MongoDB (frontend no longer sends them)
        doc = await get_upload_by_id(req.upload_id)
        observation_details = doc.get("observation_details", []) if doc else []
        result = await generate_summary(req, observation_details=observation_details)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Azure OpenAI call failed: {exc}")

    interventions_by_facility = result.get("interventions_by_facility", {})
    total_interventions = result.get("total_interventions", 0)
    category_analysis = result.get("category_analysis", [])

    # Persist summaries + intervention data back into the MongoDB document
    await update_summaries(
        upload_id=req.upload_id,
        user_summary=result["user_summary"],
        manager_summary=result["manager_summary"],
        detailed_summary=result.get("detailed_summary", ""),
        interventions_by_facility=interventions_by_facility,
        total_interventions=total_interventions,
        category_analysis=category_analysis,
    )

    # Update in-memory session with intervention data
    if req.upload_id in _sessions:
        session_cd = _sessions[req.upload_id]["chart_data"]
        if isinstance(session_cd, ChartData):
            session_cd.interventions_by_facility = interventions_by_facility
            session_cd.total_interventions = total_interventions
        elif isinstance(session_cd, dict):
            session_cd["interventions_by_facility"] = interventions_by_facility
            session_cd["total_interventions"] = total_interventions

    return SummarizeResponse(
        user_summary=result["user_summary"],
        manager_summary=result["manager_summary"],
        detailed_summary=result.get("detailed_summary", ""),
        interventions_by_facility=interventions_by_facility,
        total_interventions=total_interventions,
        category_analysis=category_analysis,
    )


@app.post("/api/send-email", response_model=EmailResponse)
async def send_email_endpoint(req: EmailRequest):
    session = _sessions.get(req.upload_id)
    if not session:
        doc = await get_upload_by_id(req.upload_id)
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Upload session not found. Please re-upload the file.",
            )
        session = {
            "chart_data": ChartData(**doc["chart_data"]),
            "date_range": doc["date_range"],
        }

    chart_data = session["chart_data"]
    if isinstance(chart_data, dict):
        chart_data = ChartData(**chart_data)

    try:
        chart_images = generate_all_charts(chart_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {exc}")

    try:
        send_email(
            to_email=req.to_email,
            subject=req.subject,
            summary=req.manager_summary,
            date_range=session["date_range"],
            chart_images=chart_images,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Email sending failed: {exc}")

    return EmailResponse(success=True, message=f"Report sent to {req.to_email}")


@app.post("/api/download-report")
async def download_report(req: DownloadReportRequest):
    session = _sessions.get(req.upload_id)
    if not session:
        doc = await get_upload_by_id(req.upload_id)
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Upload session not found. Please re-upload the file.",
            )
        session = {
            "chart_data": ChartData(**doc["chart_data"]),
            "date_range": doc["date_range"],
        }

    chart_data = session["chart_data"]
    if isinstance(chart_data, dict):
        chart_data = ChartData(**chart_data)

    try:
        pdf_bytes = generate_pdf(
            chart_data=chart_data,
            summary=req.user_summary,
            date_range=session["date_range"],
            total_observations=req.total_observations,
            manager_summary=req.manager_summary,
            detailed_summary=req.detailed_summary,
            category_analysis=req.category_analysis,
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    date_str = session["date_range"].replace(" ", "_").replace("\u2013", "-")
    filename = f"HSE_Report_{date_str}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/download-comparison")
async def download_comparison(req: DownloadComparisonRequest):
    if len(req.upload_ids) < 2 or len(req.upload_ids) > 4:
        raise HTTPException(
            status_code=400,
            detail="Please select between 2 and 4 uploads for comparison.",
        )

    docs = []
    for uid in req.upload_ids:
        doc = await get_upload_by_id(uid)
        if not doc:
            raise HTTPException(status_code=404, detail=f"Upload {uid} not found.")
        docs.append(doc)

    docs.sort(key=lambda d: d.get("upload_date", ""))

    weeks = []
    for doc in docs:
        cd = ChartData(**doc["chart_data"])
        total = doc["total_observations"]
        safe = cd.safe_vs_atrisk.get("Safe", 0)
        atrisk = cd.safe_vs_atrisk.get("At Risk", 0)
        weeks.append({
            "upload_id": str(doc["_id"]),
            "date_range": doc["date_range"],
            "total_observations": total,
            "safe_count": safe,
            "atrisk_count": atrisk,
            "safe_pct": round((safe / total * 100), 1) if total else 0.0,
            "atrisk_pct": round((atrisk / total * 100), 1) if total else 0.0,
            "total_interventions": cd.total_interventions,
            "by_facility": cd.by_facility,
        })

    trend_labels = [w["date_range"] for w in weeks]
    trends = {
        "total_observations": [w["total_observations"] for w in weeks],
        "safe_pct": [w["safe_pct"] for w in weeks],
        "atrisk_pct": [w["atrisk_pct"] for w in weeks],
        "interventions": [w["total_interventions"] for w in weeks],
    }

    first, last = weeks[0], weeks[-1]

    def make_delta(label, curr_val, prev_val, good_direction="up"):
        delta = round(curr_val - prev_val, 1)
        delta_pct = round((delta / prev_val * 100), 1) if prev_val else 0.0
        return {
            "label": label, "current": curr_val, "previous": prev_val,
            "delta": delta, "delta_pct": delta_pct, "good_direction": good_direction,
        }

    delta_cards = [
        make_delta("Total Observations", last["total_observations"], first["total_observations"], "up"),
        make_delta("Safe %", last["safe_pct"], first["safe_pct"], "up"),
        make_delta("At-Risk %", last["atrisk_pct"], first["atrisk_pct"], "down"),
        make_delta("Interventions", last["total_interventions"], first["total_interventions"], "up"),
    ]

    # Generate cross-week AI narrative for the PDF
    trend_narrative = None
    try:
        weeks_analyses = []
        for doc in docs:
            weeks_analyses.append({
                "date_range": doc["date_range"],
                "total_observations": doc["total_observations"],
                "safe_pct": round(
                    doc["chart_data"].get("safe_vs_atrisk", {}).get("Safe", 0)
                    / max(doc["total_observations"], 1) * 100, 1
                ),
                "atrisk_pct": round(
                    doc["chart_data"].get("safe_vs_atrisk", {}).get("At Risk", 0)
                    / max(doc["total_observations"], 1) * 100, 1
                ),
                "total_interventions": doc["chart_data"].get("total_interventions", 0),
                "category_analysis": doc.get("category_analysis", []),
            })
        if any(w["category_analysis"] for w in weeks_analyses):
            trend_narrative = generate_cross_week_narrative(weeks_analyses)
    except Exception:
        traceback.print_exc()

    try:
        pdf_bytes = generate_comparison_pdf(weeks, delta_cards, trends, trend_labels,
                                            trend_narrative=trend_narrative)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    first_range = weeks[0]["date_range"].replace(" ", "_").replace("\u2013", "-")
    last_range = weeks[-1]["date_range"].replace(" ", "_").replace("\u2013", "-")
    filename = f"HSE_Comparison_{first_range}_to_{last_range}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# -- History -------------------------------------------------------------------

@app.get("/api/history", response_model=HistoryResponse)
async def get_history():
    docs = await get_all_uploads()
    items = [
        HistoryItem(
            upload_id=str(doc["_id"]),
            filename=doc.get("filename", "Unknown"),
            uploaded_by=doc.get("uploaded_by", "Unknown"),
            upload_date=doc.get("upload_date", ""),
            date_range=doc.get("date_range", ""),
            total_observations=doc.get("total_observations", 0),
            user_summary=doc.get("user_summary"),
            manager_summary=doc.get("manager_summary"),
            detailed_summary=doc.get("detailed_summary"),
        )
        for doc in docs
    ]
    return HistoryResponse(uploads=items)


@app.get("/api/uploads/{upload_id}")
async def get_upload_detail(upload_id: str):
    doc = await get_upload_by_id(upload_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Upload not found.")
    doc["_id"] = str(doc["_id"])
    return doc


@app.delete("/api/uploads/{upload_id}")
async def delete_upload(upload_id: str):
    deleted = await mongo_delete_upload(upload_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Upload not found.")
    _sessions.pop(upload_id, None)
    return {"detail": "Deleted successfully"}


# -- Comparison ----------------------------------------------------------------

@app.post("/api/compare", response_model=CompareResponse)
async def compare_uploads(req: CompareRequest):
    curr_doc = await get_upload_by_id(req.current_upload_id)
    prev_doc = await get_upload_by_id(req.previous_upload_id)

    if not curr_doc or not prev_doc:
        raise HTTPException(status_code=404, detail="One or both uploads not found.")

    curr_cd = ChartData(**curr_doc["chart_data"])
    prev_cd = ChartData(**prev_doc["chart_data"])

    curr_total = curr_doc["total_observations"]
    prev_total = prev_doc["total_observations"]
    curr_safe = curr_cd.safe_vs_atrisk.get("Safe", 0)
    prev_safe = prev_cd.safe_vs_atrisk.get("Safe", 0)
    curr_atrisk = curr_cd.safe_vs_atrisk.get("At Risk", 0)
    prev_atrisk = prev_cd.safe_vs_atrisk.get("At Risk", 0)

    curr_safe_pct = round((curr_safe / curr_total * 100), 1) if curr_total else 0.0
    prev_safe_pct = round((prev_safe / prev_total * 100), 1) if prev_total else 0.0
    curr_atrisk_pct = round((curr_atrisk / curr_total * 100), 1) if curr_total else 0.0
    prev_atrisk_pct = round((prev_atrisk / prev_total * 100), 1) if prev_total else 0.0

    def make_delta(label, curr_val, prev_val, good_direction="up"):
        delta = round(curr_val - prev_val, 1)
        delta_pct = round((delta / prev_val * 100), 1) if prev_val else 0.0
        return DeltaCard(
            label=label,
            current=curr_val,
            previous=prev_val,
            delta=delta,
            delta_pct=delta_pct,
            good_direction=good_direction,
        )

    delta_cards = [
        make_delta("Total Observations", curr_total, prev_total, good_direction="up"),
        make_delta("Safe %", curr_safe_pct, prev_safe_pct, good_direction="up"),
        make_delta("At-Risk %", curr_atrisk_pct, prev_atrisk_pct, good_direction="down"),
    ]

    return CompareResponse(
        current_date_range=curr_doc["date_range"],
        previous_date_range=prev_doc["date_range"],
        delta_cards=delta_cards,
        current_chart_data=curr_cd,
        previous_chart_data=prev_cd,
    )


# -- Multi-week comparison -----------------------------------------------------

@app.post("/api/multi-compare", response_model=MultiCompareResponse)
async def multi_compare(req: MultiCompareRequest):
    if len(req.upload_ids) < 2 or len(req.upload_ids) > 4:
        raise HTTPException(
            status_code=400,
            detail="Please select between 2 and 4 uploads for comparison.",
        )

    docs = []
    for uid in req.upload_ids:
        doc = await get_upload_by_id(uid)
        if not doc:
            raise HTTPException(status_code=404, detail=f"Upload {uid} not found.")
        docs.append(doc)

    # Sort by upload_date ascending so trends go left-to-right
    docs.sort(key=lambda d: d.get("upload_date", ""))

    weeks: list[WeekData] = []
    for doc in docs:
        cd = ChartData(**doc["chart_data"])
        total = doc["total_observations"]
        safe = cd.safe_vs_atrisk.get("Safe", 0)
        atrisk = cd.safe_vs_atrisk.get("At Risk", 0)
        weeks.append(WeekData(
            upload_id=str(doc["_id"]),
            date_range=doc["date_range"],
            total_observations=total,
            safe_count=safe,
            atrisk_count=atrisk,
            safe_pct=round((safe / total * 100), 1) if total else 0.0,
            atrisk_pct=round((atrisk / total * 100), 1) if total else 0.0,
            total_interventions=cd.total_interventions,
            chart_data=cd,
        ))

    # Build trend data
    trend_labels = [w.date_range for w in weeks]
    trends = {
        "total_observations": [w.total_observations for w in weeks],
        "safe_pct": [w.safe_pct for w in weeks],
        "atrisk_pct": [w.atrisk_pct for w in weeks],
        "interventions": [w.total_interventions for w in weeks],
    }

    # Delta cards: compare last vs first
    first, last = weeks[0], weeks[-1]

    def make_delta(label, curr_val, prev_val, good_direction="up"):
        delta = round(curr_val - prev_val, 1)
        delta_pct = round((delta / prev_val * 100), 1) if prev_val else 0.0
        return DeltaCard(
            label=label,
            current=curr_val,
            previous=prev_val,
            delta=delta,
            delta_pct=delta_pct,
            good_direction=good_direction,
        )

    delta_cards = [
        make_delta("Total Observations", last.total_observations, first.total_observations, "up"),
        make_delta("Safe %", last.safe_pct, first.safe_pct, "up"),
        make_delta("At-Risk %", last.atrisk_pct, first.atrisk_pct, "down"),
        make_delta("Interventions", last.total_interventions, first.total_interventions, "up"),
    ]

    # Generate cross-week AI narrative from saved per-week category analyses
    trend_narrative = None
    try:
        weeks_analyses = []
        for doc in docs:
            weeks_analyses.append({
                "date_range": doc["date_range"],
                "total_observations": doc["total_observations"],
                "safe_pct": round(
                    doc["chart_data"].get("safe_vs_atrisk", {}).get("Safe", 0)
                    / max(doc["total_observations"], 1) * 100, 1
                ),
                "atrisk_pct": round(
                    doc["chart_data"].get("safe_vs_atrisk", {}).get("At Risk", 0)
                    / max(doc["total_observations"], 1) * 100, 1
                ),
                "total_interventions": doc["chart_data"].get("total_interventions", 0),
                "category_analysis": doc.get("category_analysis", []),
            })
        # Only call AI if at least one week has category analysis
        if any(w["category_analysis"] for w in weeks_analyses):
            trend_narrative = generate_cross_week_narrative(weeks_analyses)
    except Exception:
        traceback.print_exc()
        # Graceful degradation: comparison still works without narrative

    return MultiCompareResponse(
        weeks=weeks,
        delta_cards=delta_cards,
        trends=trends,
        trend_labels=trend_labels,
        trend_narrative=trend_narrative,
    )
