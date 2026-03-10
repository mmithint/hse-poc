import io
from typing import Dict, List

# Must use non-interactive backend before importing pyplot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe

from models.schemas import ChartData

# Color palette
COLORS_MULTI = [
    "#1565C0", "#2E7D32", "#E65100", "#C62828",
    "#6A1B9A", "#00838F", "#D84315", "#37474F",
]
COLOR_SAFE = "#2E7D32"
COLOR_ATRISK = "#C62828"
COLOR_BLUE = "#1565C0"
BG_COLOR = "#FFFFFF"
GRID_COLOR = "#E0E0E0"
TEXT_COLOR = "#212121"
LABEL_COLOR = "#616161"


def _fig_to_bytes(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf.read()


def _apply_axes(ax, fig):
    ax.set_facecolor(BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(TEXT_COLOR)


def chart_by_facility(by_facility: Dict[str, int]) -> bytes:
    """Horizontal bar chart — Observations by Facility."""
    if not by_facility:
        return _placeholder("No facility data available")

    pairs = sorted(by_facility.items(), key=lambda x: x[1])
    facilities = [p[0] for p in pairs]
    counts = [p[1] for p in pairs]

    fig_h = max(4, len(facilities) * 0.6 + 1.8)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    _apply_axes(ax, fig)

    bars = ax.barh(facilities, counts, color=COLOR_BLUE, edgecolor="none", height=0.55)
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max(counts) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            str(count), va="center", ha="left", color=TEXT_COLOR,
            fontsize=11, fontweight="bold",
        )

    ax.set_xlabel("Number of Observations", color=LABEL_COLOR, fontsize=11)
    ax.set_title("Observations by Facility", color=TEXT_COLOR, fontsize=14, pad=14, fontweight="bold")
    ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(counts) * 1.18)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def chart_by_category(by_category: Dict[str, int]) -> bytes:
    """Horizontal bar chart — Observations by Category."""
    if not by_category:
        return _placeholder("No category data available")

    pairs = sorted(by_category.items(), key=lambda x: x[1])
    categories = [_wrap(p[0], 30) for p in pairs]
    counts = [p[1] for p in pairs]
    bar_colors = [COLORS_MULTI[i % len(COLORS_MULTI)] for i in range(len(categories))]

    fig_h = max(4, len(categories) * 0.75 + 2.0)
    fig, ax = plt.subplots(figsize=(12, fig_h))
    _apply_axes(ax, fig)

    bars = ax.barh(categories, counts, color=bar_colors, edgecolor="none", height=0.55)
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max(counts) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            str(count), va="center", ha="left", color=TEXT_COLOR,
            fontsize=11, fontweight="bold",
        )

    ax.set_xlabel("Number of Observations", color=LABEL_COLOR, fontsize=11)
    ax.set_title("Observations by Category", color=TEXT_COLOR, fontsize=14, pad=14, fontweight="bold")
    ax.tick_params(axis='y', labelsize=11, pad=8)
    ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(counts) * 1.18)
    fig.subplots_adjust(left=0.35)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def chart_top_categories(by_category: Dict[str, int], limit: int = 10) -> bytes:
    """Horizontal bar chart — Top N categories by observation count."""
    if not by_category:
        return _placeholder("No category data available")

    # Sort descending, take top `limit`
    sorted_pairs = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
    top_pairs = sorted_pairs[:limit]
    # Reverse for horizontal bar (highest at top)
    top_pairs = top_pairs[::-1]

    categories = [_wrap(p[0], 30) for p in top_pairs]
    counts = [p[1] for p in top_pairs]
    bar_colors = [COLORS_MULTI[i % len(COLORS_MULTI)] for i in range(len(categories))]

    fig_h = max(4, len(categories) * 0.75 + 2.0)
    fig, ax = plt.subplots(figsize=(12, fig_h))
    _apply_axes(ax, fig)

    bars = ax.barh(categories, counts, color=bar_colors, edgecolor="none", height=0.55)
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max(counts) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            str(count), va="center", ha="left", color=TEXT_COLOR,
            fontsize=11, fontweight="bold",
        )

    ax.set_xlabel("Number of Observations", color=LABEL_COLOR, fontsize=11)
    ax.set_title("Top 10 Categories", color=TEXT_COLOR, fontsize=14, pad=14, fontweight="bold")
    ax.tick_params(axis='y', labelsize=11, pad=8)
    ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(counts) * 1.18)
    fig.subplots_adjust(left=0.35)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def chart_safe_vs_atrisk(safe_vs_atrisk: Dict[str, int]) -> tuple:
    """Donut chart — Safe vs At-Risk. Returns (white_bg_bytes, transparent_bg_bytes)."""
    safe = safe_vs_atrisk.get("Safe", 0)
    atrisk = safe_vs_atrisk.get("At Risk", 0)
    total = safe + atrisk

    if total == 0:
        placeholder = _placeholder("No observation data available")
        return placeholder, placeholder

    fig, ax = plt.subplots(figsize=(8, 6))  # 1600x1200 at 200 DPI
    _apply_axes(ax, fig)

    wedges, _, autotexts = ax.pie(
        [safe, atrisk],
        colors=[COLOR_SAFE, COLOR_ATRISK],
        autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * total)):,})",
        startangle=90,
        wedgeprops={"width": 0.3, "edgecolor": BG_COLOR, "linewidth": 4},
        pctdistance=0.85,
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(11)
        at.set_fontweight("bold")
        at.set_path_effects([pe.withStroke(linewidth=2, foreground="black")])

    # Center text — split number and label for balanced sizing
    ax.text(0, 0.04, f"{total:,}", ha="center", va="center",
            color=TEXT_COLOR, fontsize=22, fontweight="bold")
    ax.text(0, -0.09, "Total", ha="center", va="center",
            color=LABEL_COLOR, fontsize=13)

    legend_patches = [
        mpatches.Patch(color=COLOR_SAFE, label=f"Safe: {safe:,}"),
        mpatches.Patch(color=COLOR_ATRISK, label=f"At Risk: {atrisk:,}"),
    ]
    ax.legend(handles=legend_patches, loc="lower center",
              bbox_to_anchor=(0.5, -0.06), ncol=2, frameon=False,
              labelcolor=TEXT_COLOR, fontsize=11)

    ax.set_title("At-Risk vs Safe Observations", color=TEXT_COLOR, fontsize=16,
                 pad=15, fontweight="bold")
    fig.tight_layout()

    # Save white-bg version
    buf_white = io.BytesIO()
    fig.savefig(buf_white, format="png", dpi=200, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf_white.seek(0)

    # Save transparent-bg version
    buf_trans = io.BytesIO()
    fig.savefig(buf_trans, format="png", dpi=200, bbox_inches="tight",
                transparent=True)
    buf_trans.seek(0)

    plt.close(fig)
    return buf_white.read(), buf_trans.read()


def chart_top_atrisk(top_atrisk_categories: Dict[str, int]) -> bytes:
    """Vertical bar chart — Top At-Risk Categories."""
    if not top_atrisk_categories:
        return _placeholder("No at-risk observations found")

    items = list(top_atrisk_categories.items())[:8]
    categories = [item[0] for item in items]
    counts = [item[1] for item in items]

    red_shades = [
        "#B71C1C", "#C62828", "#D32F2F", "#E53935",
        "#EF5350", "#E57373", "#EF9A9A", "#FFCDD2",
    ]
    bar_colors = red_shades[:len(categories)]

    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_axes(ax, fig)

    x_pos = range(len(categories))
    bars = ax.bar(list(x_pos), counts, color=bar_colors, edgecolor="none", width=0.6)

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(counts) * 0.02,
            str(count), ha="center", va="bottom",
            color=TEXT_COLOR, fontsize=11, fontweight="bold",
        )

    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(categories, color=TEXT_COLOR, fontsize=10, rotation=45, ha='right')
    ax.set_ylabel("At-Risk Observations", color=LABEL_COLOR, fontsize=11)
    ax.set_title("Top At-Risk Categories", color=TEXT_COLOR, fontsize=14, pad=14, fontweight="bold")
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(counts) * 1.2)
    fig.subplots_adjust(bottom=0.25)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def chart_interventions_by_facility(interventions_by_facility: Dict[str, int]) -> bytes:
    """Vertical bar chart — Interventions by Facility."""
    if not interventions_by_facility:
        return _placeholder("No intervention data available")

    # Sort descending by count
    pairs = sorted(interventions_by_facility.items(), key=lambda x: x[1], reverse=True)
    facilities = [p[0] for p in pairs]
    counts = [p[1] for p in pairs]

    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_axes(ax, fig)

    x_pos = range(len(facilities))
    bars = ax.bar(list(x_pos), counts, color=COLOR_BLUE, edgecolor="none", width=0.6)

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(counts) * 0.02,
            str(count), ha="center", va="bottom",
            color=TEXT_COLOR, fontsize=11, fontweight="bold",
        )

    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(facilities, color=TEXT_COLOR, fontsize=10, rotation=45, ha='right')
    ax.set_ylabel("Interventions", color=LABEL_COLOR, fontsize=11)
    ax.set_title("Interventions by Facility", color=TEXT_COLOR, fontsize=14, pad=14, fontweight="bold")
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(counts) * 1.2)
    fig.subplots_adjust(bottom=0.25)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def chart_trend_line(labels: List[str], values: List[float], title: str,
                     color: str, y_suffix: str = "") -> bytes:
    """Line chart with filled area for a single trend metric."""
    if not labels or not values:
        return _placeholder(f"No data for {title}")

    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_axes(ax, fig)

    x = range(len(labels))
    ax.plot(list(x), values, color=color, marker="o", linewidth=2.5,
            markersize=8, zorder=3)
    ax.fill_between(list(x), values, alpha=0.15, color=color)

    for i, v in enumerate(values):
        fmt = f"{v:.1f}{y_suffix}" if isinstance(v, float) and v % 1 != 0 else f"{int(v)}{y_suffix}"
        ax.annotate(fmt, (i, v), textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=10, fontweight="bold", color=color)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9, color=TEXT_COLOR, rotation=45, ha='right')
    ax.set_title(title, color=TEXT_COLOR, fontsize=14, pad=14, fontweight="bold")
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    if values:
        margin = (max(values) - min(values)) * 0.25 or max(values) * 0.1 or 1
        ax.set_ylim(min(values) - margin, max(values) + margin)
    fig.subplots_adjust(bottom=0.25)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def chart_grouped_facility_bars(weeks: List[dict]) -> bytes:
    """Grouped horizontal bars — one color per week, all facilities on y-axis.
    weeks: list of {"date_range": str, "by_facility": Dict[str, int]}
    """
    if not weeks:
        return _placeholder("No facility data available")

    all_facilities = []
    seen = set()
    for w in weeks:
        for f in w["by_facility"]:
            if f not in seen:
                all_facilities.append(f)
                seen.add(f)
    all_facilities.sort()

    if not all_facilities:
        return _placeholder("No facility data available")

    n_weeks = len(weeks)
    n_facilities = len(all_facilities)
    bar_height = 0.7 / n_weeks
    fig_h = max(4, n_facilities * 0.7 + 2)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    _apply_axes(ax, fig)

    week_colors = COLORS_MULTI[:n_weeks]

    for wi, w in enumerate(weeks):
        offsets = [fi - (n_weeks - 1) * bar_height / 2 + wi * bar_height
                   for fi in range(n_facilities)]
        vals = [w["by_facility"].get(f, 0) for f in all_facilities]
        ax.barh(offsets, vals, height=bar_height * 0.9,
                color=week_colors[wi], edgecolor="none", label=w["date_range"])

    ax.set_yticks(range(n_facilities))
    ax.set_yticklabels(all_facilities, fontsize=10, color=TEXT_COLOR)
    ax.set_xlabel("Observations", color=LABEL_COLOR, fontsize=11)
    ax.set_title("Observations by Facility (All Weeks)", color=TEXT_COLOR,
                 fontsize=14, pad=14, fontweight="bold")
    ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=9, facecolor="#F5F5F5", edgecolor="#E0E0E0")
    fig.tight_layout()
    return _fig_to_bytes(fig)


def generate_all_charts(chart_data: ChartData) -> Dict[str, bytes]:
    charts = {
        "chart_facility": chart_by_facility(chart_data.by_facility),
        "chart_category": chart_top_categories(chart_data.by_category),
        "chart_saferisk": None,  # filled below
        "chart_atrisk":   chart_top_atrisk(chart_data.top_atrisk_categories),
    }
    # Unpack donut chart white-bg and transparent-bg versions
    white, trans = chart_safe_vs_atrisk(chart_data.safe_vs_atrisk)
    charts["chart_saferisk"] = white
    charts["chart_saferisk_transparent"] = trans
    # Full category chart (all categories) — used below the grid when >10
    if len(chart_data.by_category) > 10:
        charts["chart_category_full"] = chart_by_category(chart_data.by_category)
    if chart_data.interventions_by_facility:
        charts["chart_interventions"] = chart_interventions_by_facility(
            chart_data.interventions_by_facility
        )
    return charts


# --- Helpers ---

def _placeholder(message: str) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.text(0.5, 0.5, message, ha="center", va="center",
            color="#9E9E9E", fontsize=13, transform=ax.transAxes)
    ax.axis("off")
    return _fig_to_bytes(fig)


def _wrap(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    words = text.split()
    lines, line = [], ""
    for word in words:
        candidate = f"{line} {word}".strip() if line else word
        if len(candidate) <= max_len:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return "\n".join(lines)
