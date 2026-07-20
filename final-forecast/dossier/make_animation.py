#!/usr/bin/env python3
"""Data-driven GIF animation of the championship probability trajectory.

Honest scope note: this is a matplotlib animation of real numbers, not an
AI-generated video (no video-generation model is available in this
environment/session -- no Sora/Veo-class connector). It is a genuine
animation, rendered frame by frame from the same data as the static charts,
interpolated smoothly between the three checkpoints (pre-match, halftime,
minute 82) so the trend reads as motion rather than three dots.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")

with open(os.path.join(HERE, "master_data.json")) as f:
    D = json.load(f)

SPAIN = "#2a78d6"
ARG = "#eb6834"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial"],
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})

# Checkpoint minutes and values (use match-minute as x, not categorical)
minutes = [0, 45, 82]
spain_vals = [c["spain_title"] * 100 for c in D["checkpoints"]]
arg_vals = [c["argentina_title"] * 100 for c in D["checkpoints"]]
labels = [c["label"] for c in D["checkpoints"]]

# Smooth interpolation: PCHIP if scipy is available, otherwise linear.
def pchip_or_linear(x, y, xf):
    try:
        from scipy.interpolate import PchipInterpolator
        return PchipInterpolator(x, y)(xf)
    except ImportError:
        return np.interp(xf, x, y)

xf = np.linspace(0, 82, 240)
spain_f = pchip_or_linear(minutes, spain_vals, xf)
arg_f = pchip_or_linear(minutes, arg_vals, xf)

fig, ax = plt.subplots(figsize=(8.5, 5), dpi=110)
ax.set_xlim(0, 90)
ax.set_ylim(35, 62)
ax.set_xlabel("Match minute")
ax.set_ylabel("Probability of lifting the trophy")
ax.yaxis.set_major_formatter(mticker.PercentFormatter())
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color(GRID)
ax.spines["bottom"].set_color("#c3c2b7")
ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
ax.axhline(50, color="#898781", linewidth=1, linestyle=(0, (2, 2)), zorder=1)
ax.set_title("Spain vs Argentina -- title probability as the match unfolds",
              fontsize=13, fontweight="bold", loc="left")

line_spain, = ax.plot([], [], color=SPAIN, linewidth=2.8, zorder=3, label="Spain")
line_arg, = ax.plot([], [], color=ARG, linewidth=2.8, zorder=3, label="Argentina")
dot_spain, = ax.plot([], [], "o", color=SPAIN, markersize=9,
                      markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=4)
dot_arg, = ax.plot([], [], "o", color=ARG, markersize=9,
                    markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=4)
txt_spain = ax.text(0, 0, "", color=SPAIN, fontsize=11, fontweight="bold")
txt_arg = ax.text(0, 0, "", color=ARG, fontsize=11, fontweight="bold")
minute_txt = ax.text(0.02, 0.94, "", transform=ax.transAxes, fontsize=12,
                      fontweight="bold", color=INK2)
ax.legend(loc="upper right", frameon=False, fontsize=11)

# vertical checkpoint markers
for m, l in zip(minutes, labels):
    ax.axvline(m, color=GRID, linewidth=1, zorder=0)
    ax.text(m, 36, l, fontsize=8, color="#898781", rotation=90, va="bottom",
            ha="right" if m > 0 else "left")

N_FRAMES = 150
HOLD_FRAMES = 25  # pause at the end on the final value


def frame_idx(i):
    if i < N_FRAMES:
        return int(i / N_FRAMES * (len(xf) - 1))
    return len(xf) - 1


def update(i):
    idx = frame_idx(i)
    x = xf[: idx + 1]
    line_spain.set_data(x, spain_f[: idx + 1])
    line_arg.set_data(x, arg_f[: idx + 1])
    dot_spain.set_data([xf[idx]], [spain_f[idx]])
    dot_arg.set_data([xf[idx]], [arg_f[idx]])
    txt_spain.set_position((xf[idx] + 1.5, spain_f[idx] + 0.4))
    txt_spain.set_text(f"{spain_f[idx]:.1f}%")
    txt_arg.set_position((xf[idx] + 1.5, arg_f[idx] - 1.2))
    txt_arg.set_text(f"{arg_f[idx]:.1f}%")
    minute_txt.set_text(f"Minute {xf[idx]:.0f}'  --  score 0-0")
    return line_spain, line_arg, dot_spain, dot_arg, txt_spain, txt_arg, minute_txt


anim = FuncAnimation(fig, update, frames=N_FRAMES + HOLD_FRAMES,
                      interval=45, blit=False)

out_path = os.path.join(CHARTS, "probability_evolution.gif")
anim.save(out_path, writer=PillowWriter(fps=22))
plt.close(fig)
print("Wrote", out_path)
print("Size:", os.path.getsize(out_path) / 1024, "KB")
