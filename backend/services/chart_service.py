import io
from typing import Dict

# Must use non-interactive backend before importing pyplot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from models.schemas import ChartData

# Color palette
COLORS_MULTI = [
    "#2196F3", "#4CAF50", "#FF9800", "#F44336",
    "#9C27B0", "#00BCD4", "#FF5722", "#607D8B",
]
COLOR_SAFE = "#4CAF50"
COLOR_ATRISK = "#F44336"
COLOR_BLUE = "#2196F3"
BG_COLOR = "#1e1e2e"
GRID_COLOR = "#2d2d44"
TEXT_COLOR = "white"


def _fig_to_bytes(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    return buf.read()


def _apply_dark_axes(ax, fig):
    ax.set_facecolor(BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.spines[:].set_visible(False)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(TEXT_COLOR)


def chart_by_facility(by_facility: Dict[str, int]) -> bytes:
    """Horizontal bar chart — Observations by Facility."""
    if not by_facility:
        return _placeholder("No facility data available")

    pairs = sorted(by_facility.items(), key=lambda x: x[1])
    facilities = [p[0] for p in pairs]
    counts = [p[1] for p in pairs]

    fig_h = max(4, len(facilities) * 0.55 + 1.5)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    _apply_dark_axes(ax, fig)

    bars = ax.barh(facilities, counts, color=COLOR_BLUE, edgecolor="none", height=0.6)
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max(counts) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            str(count), va="center", ha="left", color=TEXT_COLOR, fontsize=9,
        )

    ax.set_xlabel("Number of Observations", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Observations by Facility", color=TEXT_COLOR, fontsize=13, pad=12, fontweight="bold")
    ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(counts) * 1.15)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def chart_by_category(by_category: Dict[str, int]) -> bytes:
    """Horizontal bar chart — Observations by Category."""
    if not by_category:
        return _placeholder("No category data available")

    pairs = sorted(by_category.items(), key=lambda x: x[1])
    categories = [_wrap(p[0], 22) for p in pairs]
    counts = [p[1] for p in pairs]
    colors = [COLORS_MULTI[i % len(COLORS_MULTI)] for i in range(len(categories))]

    fig_h = max(4, len(categories) * 0.6 + 1.5)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    _apply_dark_axes(ax, fig)

    bars = ax.barh(categories, counts, color=colors, edgecolor="none", height=0.6)
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + max(counts) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            str(count), va="center", ha="left", color=TEXT_COLOR, fontsize=9,
        )

    ax.set_xlabel("Number of Observations", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Observations by Category", color=TEXT_COLOR, fontsize=13, pad=12, fontweight="bold")
    ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(counts) * 1.15)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def chart_safe_vs_atrisk(safe_vs_atrisk: Dict[str, int]) -> bytes:
    """Donut chart — Safe vs At-Risk."""
    safe = safe_vs_atrisk.get("Safe", 0)
    atrisk = safe_vs_atrisk.get("At Risk", 0)
    total = safe + atrisk

    if total == 0:
        return _placeholder("No observation data available")

    fig, ax = plt.subplots(figsize=(7, 7))
    _apply_dark_axes(ax, fig)

    wedges, _, autotexts = ax.pie(
        [safe, atrisk],
        colors=[COLOR_SAFE, COLOR_ATRISK],
        autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct / 100 * total))})",
        startangle=90,
        wedgeprops={"width": 0.55, "edgecolor": BG_COLOR, "linewidth": 3},
        pctdistance=0.75,
    )
    for at in autotexts:
        at.set_color(TEXT_COLOR)
        at.set_fontsize(11)
        at.set_fontweight("bold")

    ax.text(0, 0, f"{total}\nTotal", ha="center", va="center",
            color=TEXT_COLOR, fontsize=16, fontweight="bold")

    legend_patches = [
        mpatches.Patch(color=COLOR_SAFE, label=f"Safe: {safe:,}"),
        mpatches.Patch(color=COLOR_ATRISK, label=f"At Risk: {atrisk:,}"),
    ]
    ax.legend(handles=legend_patches, loc="lower center",
              bbox_to_anchor=(0.5, -0.06), ncol=2,
              labelcolor=TEXT_COLOR, facecolor="#2d2d44", edgecolor="none",
              fontsize=11)

    ax.set_title("At-Risk vs Safe Observations", color=TEXT_COLOR, fontsize=13,
                 pad=14, fontweight="bold")
    fig.tight_layout()
    return _fig_to_bytes(fig)


def chart_top_atrisk(top_atrisk_categories: Dict[str, int]) -> bytes:
    """Vertical bar chart — Top At-Risk Categories."""
    if not top_atrisk_categories:
        return _placeholder("No at-risk observations found")

    items = list(top_atrisk_categories.items())[:8]
    categories = [_wrap(item[0], 14) for item in items]
    counts = [item[1] for item in items]

    red_shades = [
        "#B71C1C", "#C62828", "#D32F2F", "#E53935",
        "#EF5350", "#E57373", "#EF9A9A", "#FFCDD2",
    ]
    colors = red_shades[:len(categories)]

    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_dark_axes(ax, fig)

    x_pos = range(len(categories))
    bars = ax.bar(list(x_pos), counts, color=colors, edgecolor="none", width=0.65)

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(counts) * 0.02,
            str(count), ha="center", va="bottom",
            color=TEXT_COLOR, fontsize=10, fontweight="bold",
        )

    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(categories, color=TEXT_COLOR, fontsize=9)
    ax.set_ylabel("At-Risk Observations", color=TEXT_COLOR, fontsize=10)
    ax.set_title("Top At-Risk Categories", color=TEXT_COLOR, fontsize=13, pad=12, fontweight="bold")
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(counts) * 1.18)
    fig.tight_layout()
    return _fig_to_bytes(fig)


def generate_all_charts(chart_data: ChartData) -> Dict[str, bytes]:
    return {
        "chart_facility": chart_by_facility(chart_data.by_facility),
        "chart_category": chart_by_category(chart_data.by_category),
        "chart_saferisk": chart_safe_vs_atrisk(chart_data.safe_vs_atrisk),
        "chart_atrisk":   chart_top_atrisk(chart_data.top_atrisk_categories),
    }


# --- Helpers ---

def _placeholder(message: str) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.text(0.5, 0.5, message, ha="center", va="center",
            color="#888", fontsize=13, transform=ax.transAxes)
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
