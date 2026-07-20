#!/usr/bin/env python3
"""Static PNG charts for the dossier, built with matplotlib against the
dataviz skill's validated palette (references/palette.md):
  Spain = categorical slot 1 (blue #2a78d6), Argentina = slot 6 (orange
  #eb6834) -- non-adjacent slots, safe CVD separation. Draw/neutral = muted
  gray #898781. One hue axis, thin marks, legend always present, direct
  labels on the headline figures.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")
os.makedirs(CHARTS, exist_ok=True)

with open(os.path.join(HERE, "master_data.json")) as f:
    D = json.load(f)

# --- palette ---
SPAIN = "#2a78d6"
ARG = "#eb6834"
DRAW = "#898781"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK2,
    "text.color": INK,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def style_axes(ax, hide_y=False):
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    if hide_y:
        ax.spines["left"].set_visible(False)
        ax.yaxis.set_visible(False)


# ============================================================
# 1. Championship probability evolution across checkpoints
# ============================================================
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
labels = [c["label"] for c in D["checkpoints"]]
x = np.arange(len(labels))
spain = [c["spain_title"] * 100 for c in D["checkpoints"]]
arg = [c["argentina_title"] * 100 for c in D["checkpoints"]]

ax.plot(x, spain, color=SPAIN, linewidth=2.5, marker="o", markersize=8,
        markerfacecolor=SPAIN, markeredgecolor=SURFACE, markeredgewidth=1.5,
        zorder=3, label="Spain")
ax.plot(x, arg, color=ARG, linewidth=2.5, marker="o", markersize=8,
        markerfacecolor=ARG, markeredgecolor=SURFACE, markeredgewidth=1.5,
        zorder=3, label="Argentina")
ax.axhline(50, color=MUTED, linewidth=1, linestyle=(0, (2, 2)), zorder=1)
ax.text(len(labels) - 1 + 0.08, 50, "coin flip", fontsize=9, color=MUTED,
        va="center")

for i, (s, a) in enumerate(zip(spain, arg)):
    ax.annotate(f"{s:.1f}%", (i, s), textcoords="offset points",
                xytext=(0, 10), ha="center", fontsize=10, color=SPAIN,
                fontweight="bold")
    ax.annotate(f"{a:.1f}%", (i, a), textcoords="offset points",
                xytext=(0, -16), ha="center", fontsize=10, color=ARG,
                fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels([f"{l}\n({c['score_at_checkpoint']})"
                     for l, c in zip(labels, D["checkpoints"])], fontsize=10)
ax.set_ylim(30, 65)
ax.set_ylabel("Probability of lifting the trophy")
ax.yaxis.set_major_formatter(mticker.PercentFormatter())
style_axes(ax)
ax.legend(loc="upper right", frameon=False, fontsize=11)
ax.set_title("Championship probability, checkpoint by checkpoint",
              fontsize=14, fontweight="bold", loc="left", pad=14)
fig.text(0.01, -0.02,
          "Spain vs Argentina, 2026 World Cup final. Every scoreless minute "
          "narrows Spain's edge and funnels the match toward penalties.",
          fontsize=9, color=INK2)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS, "01_probability_evolution.png"),
            bbox_inches="tight")
plt.close(fig)

# ============================================================
# 2. Path-to-title stacked bars (regulation / ET / penalties)
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(12, 5), dpi=200, sharey=True)
STAGE_COLORS = {"regulation": SPAIN, "extra_time": "#5598e7", "penalties": "#b7d3f6"}
STAGE_LABELS = {"regulation": "Regulation", "extra_time": "Extra time", "penalties": "Penalties"}

for ax, cp in zip(axes, D["checkpoints"]):
    teams = ["Spain", "Argentina"]
    paths = [cp["path_spain"], cp["path_argentina"]]
    colors_by_team = [SPAIN, ARG]
    bottom = [0, 0]
    for stage in ["regulation", "extra_time", "penalties"]:
        vals = [paths[0][stage] * 100, paths[1][stage] * 100]
        alpha = {"regulation": 1.0, "extra_time": 0.62, "penalties": 0.32}[stage]
        bars = ax.bar(teams, vals, bottom=bottom,
                       color=[colors_by_team[0], colors_by_team[1]],
                       alpha=alpha, width=0.55,
                       edgecolor=SURFACE, linewidth=2, zorder=3)
        for i, v in enumerate(vals):
            if v > 2.5:
                ax.text(i, bottom[i] + v / 2, f"{v:.1f}", ha="center",
                        va="center", fontsize=8.5, color=INK,
                        fontweight="bold")
        bottom = [b + v for b, v in zip(bottom, vals)]
    style_axes(ax)
    ax.set_title(f"{cp['label']}\n({cp['score_at_checkpoint']})", fontsize=11)
    ax.set_ylim(0, 65)

axes[0].set_ylabel("Title probability (%)")
handles = [plt.Rectangle((0, 0), 1, 1, facecolor=MUTED, alpha=a, edgecolor=SURFACE)
           for a in [1.0, 0.62, 0.32]]
fig.legend(handles, [STAGE_LABELS[s] for s in ["regulation", "extra_time", "penalties"]],
           loc="upper center", ncol=3, frameon=False, fontsize=10,
           bbox_to_anchor=(0.5, 1.06))
fig.suptitle("Path to the trophy: regulation vs. extra time vs. penalties",
             fontsize=14, fontweight="bold", x=0.02, ha="left", y=1.12)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS, "02_path_to_title.png"), bbox_inches="tight")
plt.close(fig)

# ============================================================
# 3. Scoreline probability heatmap (pre-match grid)
# ============================================================
fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=200)
grid = D["checkpoints"][0]["score_grid"]
N = 5
mat = np.zeros((N, N))
for k, v in grid.items():
    a, b = map(int, k.split("-"))
    if a < N and b < N:
        mat[a, b] = v * 100

im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=mat.max(), origin="upper")
ax.set_xticks(range(N))
ax.set_yticks(range(N))
ax.set_xlabel("Argentina goals")
ax.set_ylabel("Spain goals")
ax.set_title("Pre-match scoreline probability grid (90 min)",
              fontsize=13, fontweight="bold", loc="left", pad=12)
for i in range(N):
    for j in range(N):
        val = mat[i, j]
        color = "white" if val > mat.max() * 0.55 else INK
        ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                fontsize=9, color=color)
ax.set_xticks(np.arange(-0.5, N, 1), minor=True)
ax.set_yticks(np.arange(-0.5, N, 1), minor=True)
ax.grid(which="minor", color=SURFACE, linewidth=2)
ax.tick_params(which="minor", length=0)
for spine in ax.spines.values():
    spine.set_visible(False)
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Probability (%)", color=INK2)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS, "03_scoreline_heatmap.png"), bbox_inches="tight")
plt.close(fig)

# ============================================================
# 4. Sensitivity tornado: blend weights + shootout assumption
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=200)

# 4a. blend-weight scenarios
ax = axes[0]
scen_order = ["scenario_model_heavy", "base_case", "scenario_market_heavy"]
scen_labels = ["Model-heavy\n(mkt30/pub40/elo30)", "Base case\n(mkt55/pub30/elo15)",
               "Market-heavy\n(mkt80/pub15/elo5)"]
spain_vals = [D["scenarios"][s]["spain_title"] * 100 for s in scen_order]
y = np.arange(len(scen_order))
ax.barh(y, spain_vals, color=SPAIN, height=0.5, zorder=3)
ax.axvline(50, color=MUTED, linestyle=(0, (2, 2)), linewidth=1)
for i, v in enumerate(spain_vals):
    ax.text(v + 0.4, i, f"{v:.1f}%", va="center", fontsize=10, color=SPAIN,
            fontweight="bold")
ax.set_yticks(y)
ax.set_yticklabels(scen_labels, fontsize=9.5)
ax.set_xlim(50, 62)
ax.set_xlabel("Spain title probability (%), pre-match")
style_axes(ax)
ax.set_title("Blend-weight sensitivity", fontsize=12, fontweight="bold", loc="left")

# 4b. shootout assumption sweep at minute 82
ax = axes[1]
sweep = D["checkpoints"][2]["penalty_sensitivity"]
pens = [s["pen_arg"] * 100 for s in sweep]
spain_t = [s["esp_title"] * 100 for s in sweep]
arg_t = [s["arg_title"] * 100 for s in sweep]
ax.plot(pens, spain_t, color=SPAIN, marker="o", linewidth=2.5, label="Spain")
ax.plot(pens, arg_t, color=ARG, marker="o", linewidth=2.5, label="Argentina")
ax.axhline(50, color=MUTED, linestyle=(0, (2, 2)), linewidth=1)
crossover = 63  # approx from sweep
ax.axvline(crossover, color=MUTED, linestyle=":", linewidth=1)
ax.text(crossover + 0.5, 44, "favorite\nflips ~63%", fontsize=8.5, color=INK2)
ax.set_xlabel("Argentina's assumed shootout win probability (%)")
ax.set_ylabel("Title probability (%)")
style_axes(ax)
ax.legend(loc="center left", frameon=False, fontsize=10)
ax.set_title("Minute-82 shootout sensitivity", fontsize=12, fontweight="bold",
             loc="left")

fig.suptitle("Where the estimate is fragile: two sensitivity sweeps",
              fontsize=14, fontweight="bold", x=0.01, ha="left", y=1.04)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS, "04_sensitivity_tornado.png"), bbox_inches="tight")
plt.close(fig)

# ============================================================
# 5. Funnel diagram: pre-match -> extra time -> penalties
# ============================================================
fig, ax = plt.subplots(figsize=(8, 5.5), dpi=200)
stages = ["Kickoff\n(100%)"] + [
    f"{cp['label']}\nreaches ET: {cp['reach_et']:.0%}" for cp in D["checkpoints"]
]
funnel_vals = [1.0] + [cp["reach_et"] for cp in D["checkpoints"]]
pen_vals = [None, None, None, D["checkpoints"][2]["reach_pens"]]

colors = ["#c3c2b7", "#86b6ef", "#5598e7", "#2a78d6"]
y_pos = np.arange(len(stages))
widths = [v * 8 for v in funnel_vals]
for i, (w, c) in enumerate(zip(widths, colors)):
    ax.barh(i, w, left=-w / 2, height=0.6, color=c, zorder=3,
            edgecolor=SURFACE, linewidth=1.5)
    ax.text(0, i, f"{funnel_vals[i]:.0%}", ha="center", va="center",
            fontsize=11, fontweight="bold",
            color="white" if funnel_vals[i] > 0.4 else INK)
ax.set_yticks(y_pos)
ax.set_yticklabels(stages, fontsize=10)
ax.invert_yaxis()
ax.set_xlim(-4.2, 4.2)
ax.xaxis.set_visible(False)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_title("The funnel effect: chance the match reaches extra time",
              fontsize=13, fontweight="bold", loc="left", pad=14)
fig.text(0.01, -0.02,
          "At minute 82, still 0-0, a ~51% chance this final reaches a "
          "penalty shootout -- where Spain's historical record (1 of 5) "
          "trails Argentina's (6 of 7).", fontsize=9, color=INK2, wrap=True)
fig.tight_layout()
fig.savefig(os.path.join(CHARTS, "05_funnel.png"), bbox_inches="tight")
plt.close(fig)

print("Wrote 5 charts to", CHARTS)
for f in sorted(os.listdir(CHARTS)):
    print(" -", f)
