import io
from typing import Dict, List
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from models.schemas import ChartData
from services.chart_service import (
    generate_all_charts, chart_trend_line, chart_grouped_facility_bars,
)

# -- Palette -------------------------------------------------------------------
NAVY       = colors.HexColor("#1a237e")
BLUE       = colors.HexColor("#1565C0")
LIGHT_BLUE = colors.HexColor("#E8EAF6")
GREEN      = colors.HexColor("#2E7D32")
RED        = colors.HexColor("#C62828")
ORANGE     = colors.HexColor("#E65100")
PURPLE     = colors.HexColor("#6A1B9A")
DARK_GRAY  = colors.HexColor("#212121")
MID_GRAY   = colors.HexColor("#616161")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
WHITE      = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm


# -- Styles --------------------------------------------------------------------
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
    total: int, safe: int, atrisk: int, page_width: float,
    total_interventions: int = 0,
) -> Table:
    """5-column KPI strip."""
    s = _styles()
    atrisk_pct = f"{atrisk / total * 100:.1f}%" if total else "0.0%"

    def cell(value, label, val_color):
        return [
            Paragraph(f'<font color="{val_color}">{value}</font>', s["kpi_value"]),
            Spacer(1, 2),
            Paragraph(label, s["kpi_label"]),
        ]

    col_w = (page_width - 2 * MARGIN) / 5
    data = [[
        cell(f"{total:,}",   "Total Observations",    "#1565C0"),
        cell(f"{safe:,}",    "Safe Observations",     "#2E7D32"),
        cell(f"{atrisk:,}",  "At-Risk Observations",  "#C62828"),
        cell(atrisk_pct,     "At-Risk Rate",          "#E65100"),
        cell(f"{total_interventions:,}", "Interventions", "#6A1B9A"),
    ]]
    tbl = Table(data, colWidths=[col_w] * 5)
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

    lines = [ln for ln in summary_text.strip().splitlines()]
    paragraphs = []
    for ln in lines:
        if ln.strip():
            paragraphs.append(Paragraph(xml_escape(ln.strip()), s["body"]))
        else:
            paragraphs.append(Spacer(1, 6))

    if not paragraphs:
        paragraphs = [Spacer(1, 6)]

    # One row per flowable so the table can split across pages
    data = [[p] for p in paragraphs]
    tbl = Table(data, colWidths=[col_w])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), LIGHT_BLUE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        # Extra padding on first and last rows
        ("TOPPADDING",   (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING",(0, -1), (-1, -1), 12),
        ("ROUNDEDCORNERS", [4]),
        # Left accent bar
        ("LINEBEFORE", (0, 0), (0, -1), 4, NAVY),
    ]))
    return tbl


def _chart_grid(chart_images: Dict[str, bytes], page_width: float) -> List:
    """2x2 grid of main charts + full-width interventions chart below. Returns list of flowables."""
    usable = page_width - 2 * MARGIN
    cell_w = usable / 2 - 0.3 * cm
    cell_h = cell_w * 0.72

    labels = {
        "chart_facility": "Observations by Facility",
        "chart_category": "Top 10 Categories",
        "chart_saferisk": "At-Risk vs Safe",
        "chart_atrisk":   "Top At-Risk Categories",
    }
    s = _styles()

    def chart_cell(cid: str) -> list:
        img_bytes = chart_images.get(cid, b"")
        if not img_bytes:
            return [Paragraph("No data", s["body"])]
        img = Image(io.BytesIO(img_bytes), width=cell_w, height=cell_h)
        label = Paragraph(labels.get(cid, cid), ParagraphStyle(
            "chart_label", fontSize=8, textColor=NAVY, fontName="Helvetica-Bold",
            leading=10, spaceAfter=3, textTransform="uppercase", letterSpacing=0.5,
        ))
        return [label, img]

    data = [
        [chart_cell("chart_facility"), chart_cell("chart_category")],
        [chart_cell("chart_saferisk"), chart_cell("chart_atrisk")],
    ]
    grid_tbl = Table(data, colWidths=[cell_w + 0.3 * cm, cell_w + 0.3 * cm],
                     rowHeights=None)
    grid_tbl.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))

    flowables = [grid_tbl]

    # Full-width "All Categories" chart (only when >10 categories)
    if "chart_category_full" in chart_images and chart_images["chart_category_full"]:
        full_w = usable
        full_h = full_w * 0.55
        cat_label = Paragraph("All Categories", ParagraphStyle(
            "chart_label_catfull", fontSize=8, textColor=NAVY, fontName="Helvetica-Bold",
            leading=10, spaceAfter=3, textTransform="uppercase", letterSpacing=0.5,
        ))
        cat_img = Image(
            io.BytesIO(chart_images["chart_category_full"]),
            width=full_w, height=full_h,
        )
        flowables.append(Spacer(1, 0.4 * cm))
        flowables.append(cat_label)
        flowables.append(cat_img)

    # Full-width interventions chart
    if "chart_interventions" in chart_images and chart_images["chart_interventions"]:
        full_w = usable
        full_h = full_w * 0.4
        interventions_label = Paragraph("Interventions by Facility", ParagraphStyle(
            "chart_label_full", fontSize=8, textColor=NAVY, fontName="Helvetica-Bold",
            leading=10, spaceAfter=3, textTransform="uppercase", letterSpacing=0.5,
        ))
        interventions_img = Image(
            io.BytesIO(chart_images["chart_interventions"]),
            width=full_w, height=full_h,
        )
        flowables.append(Spacer(1, 0.4 * cm))
        flowables.append(interventions_label)
        flowables.append(interventions_img)

    return flowables


def generate_pdf(
    chart_data: ChartData,
    summary: str,
    date_range: str,
    total_observations: int,
    manager_summary: str = "",
    detailed_summary: str = "",
) -> bytes:
    """
    Build a full HSE report PDF and return as bytes.
    Structure:
      - Header banner (title + date range)
      - KPI strip (5 metrics)
      - Executive Summary section
      - Charts section (2x2 grid + interventions)
      - Detailed Analysis section (if provided)
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
        title=f"HSE Observation Report \u2013 {date_range}",
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
        _kpi_table(total_observations, safe, atrisk, page_w,
                   total_interventions=chart_data.total_interventions),
        Spacer(1, 0.6 * cm),

        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")),
        Spacer(1, 0.25 * cm),
        Paragraph("Executive Summary", s["section_heading"]),
        Spacer(1, 0.15 * cm),
        _summary_table(summary, page_w),
    ]

    # Manager Report section (if provided)
    if manager_summary and manager_summary.strip():
        story.extend([
            Spacer(1, 0.6 * cm),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")),
            Spacer(1, 0.25 * cm),
            Paragraph("Manager Report", s["section_heading"]),
            Spacer(1, 0.15 * cm),
            _summary_table(manager_summary, page_w),
        ])

    story.extend([
        Spacer(1, 0.6 * cm),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")),
        Spacer(1, 0.25 * cm),
        Paragraph("Observation Charts", s["section_heading"]),
        Spacer(1, 0.15 * cm),
        *_chart_grid(chart_images, page_w),
    ])

    # Detailed Analysis section
    if detailed_summary and detailed_summary.strip():
        story.extend([
            Spacer(1, 0.6 * cm),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")),
            Spacer(1, 0.25 * cm),
            Paragraph("Detailed Analysis", s["section_heading"]),
            Spacer(1, 0.15 * cm),
            _summary_table(detailed_summary, page_w),
        ])

    doc.build(story)
    buf.seek(0)
    return buf.read()


# -- Comparison PDF helpers ----------------------------------------------------

def _delta_cards_table(delta_cards: list, page_width: float) -> Table:
    """4-column table showing delta metrics with color-coded values."""
    s = _styles()
    col_w = (page_width - 2 * MARGIN) / len(delta_cards)

    def _fmt(v):
        if isinstance(v, float) and v % 1 != 0:
            return f"{v:.1f}%"
        return f"{int(v):,}"

    dcval_style = ParagraphStyle("dcval", fontSize=18, fontName="Helvetica-Bold",
                                  leading=22, alignment=TA_CENTER)
    dcdelta_style = ParagraphStyle("dcdelta", fontSize=9, fontName="Helvetica-Bold",
                                    leading=12, alignment=TA_CENTER)

    cells = []
    for card in delta_cards:
        is_up = card["delta"] > 0
        is_neutral = card["delta"] == 0
        is_good = None if is_neutral else (
            is_up if card["good_direction"] == "up" else not is_up
        )
        delta_color = "#616161" if is_neutral else ("#2E7D32" if is_good else "#C62828")
        arrow = "\u2014" if is_neutral else ("\u25B2" if is_up else "\u25BC")
        delta_text = f'{arrow} {abs(card["delta_pct"]):.1f}%'

        cells.append([
            Paragraph(card["label"].upper(), s["kpi_label"]),
            Spacer(1, 2),
            Paragraph(f'<font color="#1565C0"><b>{_fmt(card["current"])}</b></font>',
                      dcval_style),
            Spacer(1, 2),
            Paragraph(f'<font color="{delta_color}">{delta_text}</font>',
                      dcdelta_style),
        ])

    data = [cells]
    tbl = Table(data, colWidths=[col_w] * len(delta_cards))
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


def _week_comparison_table(weeks: list, page_width: float) -> Table:
    """One row per week with KPI columns."""
    s = _styles()
    usable = page_width - 2 * MARGIN
    headers = ["Period", "Total Obs", "Safe", "At-Risk", "Safe %", "At-Risk %", "Interventions"]
    col_w = usable / len(headers)

    header_style = ParagraphStyle("wch", fontSize=8, fontName="Helvetica-Bold",
                                  textColor=WHITE, leading=11, alignment=TA_CENTER)
    cell_style = ParagraphStyle("wcc", fontSize=9, fontName="Helvetica",
                                textColor=DARK_GRAY, leading=12, alignment=TA_CENTER)
    period_style = ParagraphStyle("wcp", fontSize=8, fontName="Helvetica-Bold",
                                  textColor=NAVY, leading=11, alignment=TA_LEFT)

    data = [[Paragraph(h, header_style) for h in headers]]
    for w in weeks:
        data.append([
            Paragraph(w["date_range"], period_style),
            Paragraph(f'{w["total_observations"]:,}', cell_style),
            Paragraph(f'{w["safe_count"]:,}', cell_style),
            Paragraph(f'{w["atrisk_count"]:,}', cell_style),
            Paragraph(f'{w["safe_pct"]:.1f}%', cell_style),
            Paragraph(f'{w["atrisk_pct"]:.1f}%', cell_style),
            Paragraph(f'{w["total_interventions"]:,}', cell_style),
        ])

    tbl = Table(data, colWidths=[col_w] * len(headers))
    style_cmds = [
        ("BACKGROUND",   (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("BACKGROUND",   (0, 1), (-1, -1), LIGHT_GRAY),
        ("BOX",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), WHITE))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _trend_narrative_section(trend_narrative: dict, page_width: float) -> list:
    """Build flowables for the cross-week evolution section."""
    s = _styles()
    flowables = [
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")),
        Spacer(1, 0.25 * cm),
        Paragraph("Cross-Week Evolution", s["section_heading"]),
        Spacer(1, 0.15 * cm),
    ]

    # Overall narrative in a light-blue box
    narrative = trend_narrative.get("overall_narrative", "")
    if narrative:
        flowables.append(_summary_table(narrative, page_width))
        flowables.append(Spacer(1, 0.3 * cm))

    usable = page_width - 2 * MARGIN
    bullet_style = ParagraphStyle(
        "trend_bullet", fontSize=9.5, textColor=DARK_GRAY,
        fontName="Helvetica", leading=14, spaceAfter=3,
    )

    # Improvements (green bullets)
    improvements = trend_narrative.get("improvements", [])
    if improvements:
        flowables.append(Paragraph(
            '<font color="#2E7D32"><b>Improvements</b></font>',
            ParagraphStyle("imp_head", fontSize=10, fontName="Helvetica-Bold",
                           textColor=GREEN, leading=14, spaceAfter=4),
        ))
        for item in improvements:
            flowables.append(Paragraph(
                f'\u2022 {xml_escape(item)}', bullet_style,
            ))
        flowables.append(Spacer(1, 0.2 * cm))

    # Persistent risks (red bullets)
    persistent = trend_narrative.get("persistent_risks", [])
    if persistent:
        flowables.append(Paragraph(
            '<font color="#C62828"><b>Persistent Risks</b></font>',
            ParagraphStyle("risk_head", fontSize=10, fontName="Helvetica-Bold",
                           textColor=RED, leading=14, spaceAfter=4),
        ))
        for item in persistent:
            flowables.append(Paragraph(
                f'\u2022 {xml_escape(item)}', bullet_style,
            ))

    return flowables


def generate_comparison_pdf(
    weeks: list,
    delta_cards: list,
    trends: dict,
    trend_labels: list,
    trend_narrative: dict = None,
) -> bytes:
    """Build multi-week comparison PDF and return as bytes."""
    buf = io.BytesIO()

    first_range = weeks[0]["date_range"] if weeks else ""
    last_range = weeks[-1]["date_range"] if weeks else ""
    # Extract start of first week and end of last week for a clean period label
    first_start = first_range.split("\u2013")[0].strip() if "\u2013" in first_range else first_range
    last_end = last_range.split("\u2013")[-1].strip() if "\u2013" in last_range else last_range
    period = f"{first_start} \u2013 {last_end}"

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 0.5 * cm,
        title=f"HSE Multi-Week Comparison \u2013 {period}",
        author="HSE Reporting System",
    )

    s = _styles()
    page_w = PAGE_W
    usable = page_w - 2 * MARGIN

    story = [
        _header_table("HSE Multi-Week Comparison", period, page_w),
        Spacer(1, 0.5 * cm),
    ]

    # Delta cards
    story.append(Paragraph("Period-over-Period Changes", s["section_heading"]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_delta_cards_table(delta_cards, page_w))
    story.append(Spacer(1, 0.6 * cm))

    # Week comparison table
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph("Weekly KPI Breakdown", s["section_heading"]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_week_comparison_table(weeks, page_w))
    story.append(Spacer(1, 0.6 * cm))

    # Trend charts — 2x2 grid
    trend_configs = [
        ("total_observations", "Total Observations Trend", "#1565C0", ""),
        ("safe_pct",           "Safe % Trend",             "#2E7D32", "%"),
        ("atrisk_pct",         "At-Risk % Trend",          "#C62828", "%"),
        ("interventions",      "Interventions Trend",      "#6A1B9A", ""),
    ]

    trend_images = {}
    for key, title, color, suffix in trend_configs:
        vals = trends.get(key, [])
        trend_images[key] = chart_trend_line(trend_labels, vals, title, color, suffix)

    cell_w = usable / 2 - 0.3 * cm
    cell_h = cell_w * 0.55

    def _trend_cell(key: str) -> list:
        img_bytes = trend_images.get(key, b"")
        if not img_bytes:
            return [Paragraph("No data", s["body"])]
        return [Image(io.BytesIO(img_bytes), width=cell_w, height=cell_h)]

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph("Trend Charts", s["section_heading"]))
    story.append(Spacer(1, 0.15 * cm))

    trend_data = [
        [_trend_cell("total_observations"), _trend_cell("safe_pct")],
        [_trend_cell("atrisk_pct"),         _trend_cell("interventions")],
    ]
    trend_tbl = Table(trend_data, colWidths=[cell_w + 0.3 * cm, cell_w + 0.3 * cm])
    trend_tbl.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(trend_tbl)
    story.append(Spacer(1, 0.6 * cm))

    # Grouped facility bar chart (full width)
    facility_weeks = [
        {"date_range": w["date_range"], "by_facility": w.get("by_facility", {})}
        for w in weeks
    ]
    facility_img = chart_grouped_facility_bars(facility_weeks)
    if facility_img:
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")))
        story.append(Spacer(1, 0.25 * cm))
        story.append(Paragraph("Facility Comparison", s["section_heading"]))
        story.append(Spacer(1, 0.15 * cm))
        full_w = usable
        full_h = full_w * 0.45
        story.append(Image(io.BytesIO(facility_img), width=full_w, height=full_h))

    # Cross-week evolution narrative
    if trend_narrative:
        story.append(Spacer(1, 0.6 * cm))
        story.extend(_trend_narrative_section(trend_narrative, page_w))

    doc.build(story)
    buf.seek(0)
    return buf.read()
