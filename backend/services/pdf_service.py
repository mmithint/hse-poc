import io
from typing import Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models.schemas import ChartData
from services.chart_service import generate_all_charts

# ── Palette ──────────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#1a237e")
BLUE       = colors.HexColor("#1565C0")
LIGHT_BLUE = colors.HexColor("#E8EAF6")
GREEN      = colors.HexColor("#2E7D32")
RED        = colors.HexColor("#C62828")
ORANGE     = colors.HexColor("#E65100")
DARK_GRAY  = colors.HexColor("#212121")
MID_GRAY   = colors.HexColor("#616161")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
WHITE      = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm


# ── Styles ────────────────────────────────────────────────────────────────────
def _styles() -> dict:
    return {
        "title": ParagraphStyle(
            "title", fontSize=20, textColor=WHITE,
            fontName="Helvetica-Bold", leading=26, alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=10, textColor=colors.HexColor("#C5CAE9"),
            fontName="Helvetica", leading=14, alignment=TA_LEFT,
        ),
        "section_heading": ParagraphStyle(
            "section_heading", fontSize=10, textColor=NAVY,
            fontName="Helvetica-Bold", leading=14, spaceAfter=4,
            textTransform="uppercase", letterSpacing=1,
        ),
        "body": ParagraphStyle(
            "body", fontSize=9.5, textColor=DARK_GRAY,
            fontName="Helvetica", leading=15, spaceAfter=4,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value", fontSize=22, fontName="Helvetica-Bold",
            leading=26, alignment=TA_CENTER,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label", fontSize=7.5, fontName="Helvetica",
            textColor=MID_GRAY, leading=10, alignment=TA_CENTER,
            textTransform="uppercase", letterSpacing=0.5,
        ),
    }


def _header_table(title: str, date_range: str, page_width: float):
    """Dark navy header banner with title and date range."""
    s = _styles()
    data = [[
        Paragraph(title, s["title"]),
        Paragraph(f"Period: {date_range}", s["subtitle"]),
    ]]
    col_w = page_width - 2 * MARGIN
    tbl = Table(data, colWidths=[col_w * 0.65, col_w * 0.35])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",        (1, 0), (1, 0),   "RIGHT"),
        ("TOPPADDING",   (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 14),
        ("LEFTPADDING",  (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("ROUNDEDCORNERS", [6]),
    ]))
    return tbl


def _kpi_table(
    total: int, safe: int, atrisk: int, page_width: float
) -> Table:
    """4-column KPI strip."""
    s = _styles()
    atrisk_pct = f"{atrisk / total * 100:.1f}%" if total else "0.0%"

    def cell(value, label, val_color):
        return [
            Paragraph(f'<font color="{val_color}">{value}</font>', s["kpi_value"]),
            Spacer(1, 2),
            Paragraph(label, s["kpi_label"]),
        ]

    col_w = (page_width - 2 * MARGIN) / 4
    data = [[
        cell(f"{total:,}",   "Total Observations",    "#1565C0"),
        cell(f"{safe:,}",    "Safe Observations",     "#2E7D32"),
        cell(f"{atrisk:,}",  "At-Risk Observations",  "#C62828"),
        cell(atrisk_pct,     "At-Risk Rate",          "#E65100"),
    ]]
    tbl = Table(data, colWidths=[col_w] * 4)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_GRAY),
        ("BOX",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return tbl


def _summary_table(summary_text: str, page_width: float) -> Table:
    """Light blue summary box with left border accent."""
    s = _styles()
    col_w = page_width - 2 * MARGIN

    # Split on newlines to preserve the AI summary's section structure
    lines = [ln for ln in summary_text.strip().splitlines()]
    paragraphs = []
    for ln in lines:
        if ln.strip():
            paragraphs.append(Paragraph(ln.strip(), s["body"]))
        else:
            paragraphs.append(Spacer(1, 6))

    data = [[paragraphs]]
    tbl = Table(data, colWidths=[col_w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_BLUE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [4]),
        # Left accent bar
        ("LINEBEFOREEACH", (0, 0), (0, -1), 4, NAVY),
    ]))
    return tbl


def _chart_grid(chart_images: Dict[str, bytes], page_width: float) -> Table:
    """2×2 grid of chart images."""
    usable = page_width - 2 * MARGIN
    cell_w = usable / 2 - 0.3 * cm
    cell_h = cell_w * 0.62  # aspect ratio roughly matches matplotlib output

    labels = {
        "chart_facility": "Observations by Facility",
        "chart_category": "Observations by Category",
        "chart_saferisk": "At-Risk vs Safe",
        "chart_atrisk":   "Top At-Risk Categories",
    }
    s = _styles()

    def chart_cell(cid: str) -> list:
        img_bytes = chart_images.get(cid, b"")
        if not img_bytes:
            return [Paragraph("No data", s["body"])]
        img = Image(io.BytesIO(img_bytes), width=cell_w, height=cell_h)
        label = Paragraph(labels[cid], ParagraphStyle(
            "chart_label", fontSize=8, textColor=NAVY, fontName="Helvetica-Bold",
            leading=10, spaceAfter=3, textTransform="uppercase", letterSpacing=0.5,
        ))
        return [label, img]

    data = [
        [chart_cell("chart_facility"), chart_cell("chart_category")],
        [chart_cell("chart_saferisk"), chart_cell("chart_atrisk")],
    ]
    tbl = Table(data, colWidths=[cell_w + 0.3 * cm, cell_w + 0.3 * cm],
                rowHeights=None)
    tbl.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tbl


def generate_pdf(
    chart_data: ChartData,
    summary: str,
    date_range: str,
    total_observations: int,
) -> bytes:
    """
    Build a full HSE report PDF and return as bytes.
    Structure:
      - Header banner (title + date range)
      - KPI strip (4 metrics)
      - Executive Summary section
      - Charts section (2x2 grid)
      - Footer (auto page numbers via SimpleDocTemplate)
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 0.5 * cm,
        title=f"HSE Observation Report – {date_range}",
        author="HSE Reporting System",
    )

    s = _styles()
    safe    = chart_data.safe_vs_atrisk.get("Safe", 0)
    atrisk  = chart_data.safe_vs_atrisk.get("At Risk", 0)
    page_w  = PAGE_W

    chart_images = generate_all_charts(chart_data)

    story = [
        _header_table("HSE Observation Report", date_range, page_w),
        Spacer(1, 0.5 * cm),
        _kpi_table(total_observations, safe, atrisk, page_w),
        Spacer(1, 0.6 * cm),

        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")),
        Spacer(1, 0.25 * cm),
        Paragraph("Executive Summary", s["section_heading"]),
        Spacer(1, 0.15 * cm),
        _summary_table(summary, page_w),

        Spacer(1, 0.6 * cm),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")),
        Spacer(1, 0.25 * cm),
        Paragraph("Observation Charts", s["section_heading"]),
        Spacer(1, 0.15 * cm),
        _chart_grid(chart_images, page_w),
    ]

    doc.build(story)
    buf.seek(0)
    return buf.read()
