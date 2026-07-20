#!/usr/bin/env python3
"""Second batch of static charts: Elo multi-horizon trend and the audit
scorecard. Split from make_charts.py since these depend on data that lands
later in the pipeline (research agent, final result)."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

SPAIN = "#2a78d6"
ARG = "#eb6834"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})


def style_axes(ax):
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


# ============================================================
# 6. Elo multi-horizon trend
# ============================================================
with open(os.path.join(HERE, "elo_trend.json")) as f:
    elo = json.load(f)

fig, ax = plt.subplots(figsize=(11, 5.5), dpi=200)
for team, color, side in [("spain", SPAIN, "Spain"), ("argentina", ARG, "Argentina")]:
    pts = elo[team]
    dates = [np.datetime64(p["date"]) for p in pts]
    ratings = [p["rating"] for p in pts]
    ax.step(dates, ratings, where="post", color=color, linewidth=2.2, label=side, zorder=3)
    ax.scatter(dates, ratings, color=color, s=28, zorder=4, edgecolor=SURFACE, linewidth=1)

ax.scatter([np.datetime64("2024-07-14")], [2150], s=0)  # keep autoscale sane
ax.annotate("Both win continental titles\non the same day", xy=(np.datetime64("2024-07-14"), 2160),
            xytext=(np.datetime64("2024-01-01"), 2230),
            fontsize=8.5, color=INK2,
            arrowprops=dict(arrowstyle="->", color=MUTED, lw=1))
ax.annotate("World Cup final:\nSpain 1-0 Argentina (AET)", xy=(np.datetime64("2026-07-19"), 2259),
            xytext=(np.datetime64("2025-09-01"), 2270),
            fontsize=8.5, color=INK2, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=SPAIN, lw=1.2))

ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
fig.autofmt_xdate(rotation=30, ha="right")
ax.set_ylabel("World Football Elo rating")
style_axes(ax)
ax.legend(loc="upper left", frameon=False, fontsize=11)
ax.set_title("36-month Elo trajectory: Spain vs Argentina",
              fontsize=14, fontweight="bold", loc="left", pad=14)
fig.text(0.01, -0.05,
          "Source: eloratings.net per-nation match history. Step lines hold "
          "flat between matches (Elo only updates on match days).",
          fontsize=8.5, color=INK2)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS, "06_elo_trend.png"), bbox_inches="tight")
plt.close(fig)

# ============================================================
# 7. Audit scorecard
# ============================================================
audit_path = os.path.join(HERE, "audit.json")
if os.path.exists(audit_path):
    with open(audit_path) as f:
        audit = json.load(f)

    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=200)
    cps = [r["checkpoint"] for r in audit["rows"]]
    briers = [r["brier_score"] for r in audit["rows"]]
    x = np.arange(len(cps))
    bars = ax.bar(x, briers, color=SPAIN, width=0.5, zorder=3)
    for i, b in enumerate(briers):
        ax.text(i, b + 0.006, f"{b:.4f}", ha="center", fontsize=10,
                fontweight="bold", color=INK)
    ax.axhline(0.25, color=MUTED, linestyle=(0, (2, 2)), linewidth=1.3)
    ax.text(len(cps) - 0.35, 0.253, "coin-flip baseline (0.250)", fontsize=9,
            color=INK2, va="bottom")
    ax.set_xticks(x)
    ax.set_xticklabels(cps, fontsize=11)
    ax.set_ylim(0, 0.30)
    ax.set_ylabel("Brier score (lower = better)")
    style_axes(ax)
    ax.set_title("Forecast accuracy vs. a coin-flip baseline",
                  fontsize=13, fontweight="bold", loc="left", pad=12)
    fig.text(0.01, -0.03,
              f"Final result: {audit['final_result_summary']}. All three checkpoints "
              "correctly favored Spain and beat the naive baseline. n=1 match -- "
              "this is not a validated calibration claim.",
              fontsize=8.5, color=INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, "07_audit_scorecard.png"), bbox_inches="tight")
    plt.close(fig)

print("Wrote 06_elo_trend.png" + (" and 07_audit_scorecard.png" if os.path.exists(audit_path) else ""))
