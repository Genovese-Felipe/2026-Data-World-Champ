#!/usr/bin/env python3
"""Builds the self-contained interactive Plotly dashboard (dashboard.html)
and, if elo_trend.json exists, includes the multi-horizon Elo trend panel
with native Plotly range-selector buttons (7d/15d/1m/.../16m/+4m steps) --
this is the closest honest match to "filtered, interactive Plotly" that can
ship as a static artifact with no backend (a strict CSP blocks any external
fetch, including a Dash/Flask server call-back endpoint).

A companion Dash app (dash_app.py) provides real Python server-side
callbacks for anyone who wants to run it locally.
"""
import json
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "master_data.json")) as f:
    D = json.load(f)

ELO_PATH = os.path.join(HERE, "elo_trend.json")
elo_data = None
if os.path.exists(ELO_PATH):
    with open(ELO_PATH) as f:
        elo_data = json.load(f)

FINAL_PATH = os.path.join(HERE, "final_result.json")
final_result = None
if os.path.exists(FINAL_PATH):
    with open(FINAL_PATH) as f:
        final_result = json.load(f)

AUDIT_PATH = os.path.join(HERE, "audit.json")
audit = None
if os.path.exists(AUDIT_PATH):
    with open(AUDIT_PATH) as f:
        audit = json.load(f)

SPAIN = "#2a78d6"
ARG = "#eb6834"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"

TEMPLATE_LAYOUT = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK),
    margin=dict(l=60, r=30, t=60, b=50),
    hoverlabel=dict(bgcolor="white", font_size=13),
)

# ---------------------------------------------------------------------
# Figure 1: probability evolution
# ---------------------------------------------------------------------
labels = [c["label"] for c in D["checkpoints"]]
minutes = [0, 45, 82]
spain_v = [c["spain_title"] * 100 for c in D["checkpoints"]]
arg_v = [c["argentina_title"] * 100 for c in D["checkpoints"]]

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=minutes, y=spain_v, mode="lines+markers+text", name="Spain",
    line=dict(color=SPAIN, width=3), marker=dict(size=11, line=dict(width=2, color=SURFACE)),
    text=[f"{v:.1f}%" for v in spain_v], textposition="top center",
    hovertemplate="Spain, %{customdata}<br>Title probability: %{y:.1f}%<extra></extra>",
    customdata=labels,
))
fig1.add_trace(go.Scatter(
    x=minutes, y=arg_v, mode="lines+markers+text", name="Argentina",
    line=dict(color=ARG, width=3), marker=dict(size=11, line=dict(width=2, color=SURFACE)),
    text=[f"{v:.1f}%" for v in arg_v], textposition="bottom center",
    hovertemplate="Argentina, %{customdata}<br>Title probability: %{y:.1f}%<extra></extra>",
    customdata=labels,
))
fig1.add_hline(y=50, line=dict(color=MUTED, dash="dot", width=1),
               annotation_text="coin flip", annotation_position="right")
for m, l in zip(minutes, labels):
    fig1.add_vline(x=m, line=dict(color=GRID, width=1))
fig1.update_layout(
    title="Championship probability, checkpoint by checkpoint",
    xaxis_title="Match minute", yaxis_title="Probability of lifting the trophy (%)",
    yaxis=dict(range=[30, 65], gridcolor=GRID),
    xaxis=dict(gridcolor=GRID, tickmode="array", tickvals=minutes,
               ticktext=[f"{l}<br>({c['score_at_checkpoint']})" for l, c in zip(labels, D["checkpoints"])]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"),
    **TEMPLATE_LAYOUT,
)

# ---------------------------------------------------------------------
# Figure 2: path-to-title, dropdown selects checkpoint
# ---------------------------------------------------------------------
def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


stages = ["regulation", "extra_time", "penalties"]
stage_labels = {"regulation": "Regulation", "extra_time": "Extra time", "penalties": "Penalties"}
stage_alpha = {"regulation": 1.0, "extra_time": 0.8, "penalties": 0.4}

fig2 = go.Figure()
n_cp = len(D["checkpoints"])
for cp_i, cp in enumerate(D["checkpoints"]):
    for stage in stages:
        fig2.add_trace(go.Bar(
            x=["Spain", "Argentina"],
            y=[cp["path_spain"][stage] * 100, cp["path_argentina"][stage] * 100],
            name=stage_labels[stage],
            marker=dict(color=[rgba(SPAIN, stage_alpha[stage]), rgba(ARG, stage_alpha[stage])]),
            visible=(cp_i == 0),
            legendgroup=stage,
            showlegend=(cp_i == 0),
            hovertemplate="%{x}: %{y:.1f}%<extra>" + stage_labels[stage] + "</extra>",
        ))

buttons = []
for cp_i, cp in enumerate(D["checkpoints"]):
    vis = [False] * (n_cp * 3)
    for j in range(3):
        vis[cp_i * 3 + j] = True
    buttons.append(dict(label=cp["label"], method="update",
                         args=[{"visible": vis},
                                {"title": f"Path to the trophy — {cp['label']} ({cp['score_at_checkpoint']})"}]))

fig2.update_layout(
    barmode="stack",
    title=f"Path to the trophy — {D['checkpoints'][0]['label']} ({D['checkpoints'][0]['score_at_checkpoint']})",
    yaxis=dict(title="Title probability (%)", range=[0, 65], gridcolor=GRID),
    updatemenus=[dict(type="dropdown", buttons=buttons, x=1.0, xanchor="right", y=1.18,
                       bgcolor=SURFACE, bordercolor=GRID)],
    annotations=[dict(text="Checkpoint:", x=0.78, xref="paper", y=1.19, yref="paper",
                       showarrow=False, font=dict(size=12, color=INK2))],
    **TEMPLATE_LAYOUT,
)

# ---------------------------------------------------------------------
# Figure 3: scoreline heatmap, dropdown selects checkpoint
# ---------------------------------------------------------------------
N = 5
heatmaps = []
for cp in D["checkpoints"]:
    mat = [[0.0] * N for _ in range(N)]
    for k, v in cp["score_grid"].items():
        a, b = map(int, k.split("-"))
        if a < N and b < N:
            mat[a][b] = round(v * 100, 2)
    heatmaps.append(mat)

fig3 = go.Figure(data=go.Heatmap(
    z=heatmaps[0], x=list(range(N)), y=list(range(N)),
    colorscale=[[0, "#cde2fb"], [0.5, "#5598e7"], [1, "#0d366b"]],
    text=[[f"{v:.1f}%" for v in row] for row in heatmaps[0]],
    texttemplate="%{text}", textfont=dict(size=11),
    hovertemplate="Spain %{y} - Argentina %{x}<br>%{z:.2f}%<extra></extra>",
    colorbar=dict(title="Prob (%)"),
))
buttons3 = [dict(label=cp["label"], method="update",
                  args=[{"z": [hm], "text": [[[f"{v:.1f}%" for v in row] for row in hm][0]]},
                        {"title": f"Scoreline probability grid — {cp['label']}"}])
            for cp, hm in zip(D["checkpoints"], heatmaps)]
fig3.update_layout(
    title=f"Scoreline probability grid — {D['checkpoints'][0]['label']}",
    xaxis=dict(title="Argentina goals", dtick=1),
    yaxis=dict(title="Spain goals", dtick=1),
    updatemenus=[dict(type="dropdown", buttons=buttons3, x=1.0, xanchor="right", y=1.18,
                       bgcolor=SURFACE, bordercolor=GRID)],
    **TEMPLATE_LAYOUT,
)

# ---------------------------------------------------------------------
# Figure 4: shootout sensitivity sweep
# ---------------------------------------------------------------------
sweep = D["checkpoints"][2]["penalty_sensitivity"]
pens = [s["pen_arg"] * 100 for s in sweep]
spain_t = [s["esp_title"] * 100 for s in sweep]
arg_t = [s["arg_title"] * 100 for s in sweep]

fig4 = go.Figure()
fig4.add_trace(go.Scatter(x=pens, y=spain_t, mode="lines+markers", name="Spain",
                           line=dict(color=SPAIN, width=3), marker=dict(size=9)))
fig4.add_trace(go.Scatter(x=pens, y=arg_t, mode="lines+markers", name="Argentina",
                           line=dict(color=ARG, width=3), marker=dict(size=9)))
fig4.add_hline(y=50, line=dict(color=MUTED, dash="dot", width=1))
fig4.add_vline(x=58, line=dict(color=SPAIN, dash="dash", width=1),
               annotation_text="central estimate (58%)", annotation_position="top")
fig4.update_layout(
    title="Minute-82 sensitivity: Argentina's shootout win probability",
    xaxis_title="Argentina's assumed shootout win probability (%)",
    yaxis=dict(title="Title probability (%)", gridcolor=GRID),
    **TEMPLATE_LAYOUT,
)

# ---------------------------------------------------------------------
# Figure 5: Elo multi-horizon trend (native Plotly range-selector buttons)
# ---------------------------------------------------------------------
fig5 = None
if elo_data:
    sp_pts = elo_data["spain"]
    ar_pts = elo_data["argentina"]
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=[p["date"] for p in sp_pts], y=[p["rating"] for p in sp_pts],
        mode="lines+markers", name="Spain",
        line=dict(color=SPAIN, width=2.5, shape="hv"), marker=dict(size=6),
        text=[p["context"] for p in sp_pts],
        hovertemplate="%{x}<br>Elo %{y}<br>%{text}<extra>Spain</extra>",
    ))
    fig5.add_trace(go.Scatter(
        x=[p["date"] for p in ar_pts], y=[p["rating"] for p in ar_pts],
        mode="lines+markers", name="Argentina",
        line=dict(color=ARG, width=2.5, shape="hv"), marker=dict(size=6),
        text=[p["context"] for p in ar_pts],
        hovertemplate="%{x}<br>Elo %{y}<br>%{text}<extra>Argentina</extra>",
    ))
    fig5.update_layout(
        title="World Football Elo rating trend — filter by lookback window",
        yaxis=dict(title="Elo rating", gridcolor=GRID),
        xaxis=dict(
            gridcolor=GRID,
            rangeselector=dict(
                buttons=[
                    dict(count=7, label="7d", step="day", stepmode="backward"),
                    dict(count=15, label="15d", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=2, label="2m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=4, label="4m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=9, label="9m", step="month", stepmode="backward"),
                    dict(count=12, label="12m", step="month", stepmode="backward"),
                    dict(count=16, label="16m", step="month", stepmode="backward"),
                    dict(step="all", label="all (36m)"),
                ],
                bgcolor=SURFACE, bordercolor=GRID, activecolor="#cde2fb",
                font=dict(size=11),
            ),
            rangeslider=dict(visible=True, bgcolor="#f9f9f7", bordercolor=GRID),
            type="date",
        ),
        **TEMPLATE_LAYOUT,
    )
    fig5.update_layout(margin=dict(l=60, r=30, t=110, b=80))

# ---------------------------------------------------------------------
# Figure 6: audit -- Brier score per checkpoint vs coin-flip baseline
# ---------------------------------------------------------------------
fig6 = None
if audit:
    cps = [r["checkpoint"] for r in audit["rows"]]
    briers = [r["brier_score"] for r in audit["rows"]]
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
        x=cps, y=briers, name="Forecast Brier score",
        marker=dict(color=SPAIN),
        text=[f"{b:.3f}" for b in briers], textposition="outside",
        hovertemplate="%{x}<br>Brier score: %{y:.4f}<extra></extra>",
    ))
    fig6.add_hline(y=0.25, line=dict(color=MUTED, dash="dash", width=1.5),
                   annotation_text="coin-flip baseline (0.250)",
                   annotation_position="right")
    fig6.update_layout(
        title="Forecast accuracy: Brier score vs. coin-flip baseline (lower is better)",
        yaxis=dict(title="Brier score", range=[0, 0.30], gridcolor=GRID),
        **TEMPLATE_LAYOUT,
    )

# ---------------------------------------------------------------------
# Assemble HTML
# ---------------------------------------------------------------------
import plotly.io as pio

def fig_html(fig, div_id):
    return pio.to_html(fig, include_plotlyjs=False, full_html=False, div_id=div_id,
                        config={"displaylogo": False, "responsive": True})

plotly_js = pio.to_html(go.Figure(), include_plotlyjs="inline", full_html=False)
# Extract every <script> block and keep the largest one (the plotly.js
# library bundle) -- a non-greedy single match grabs the tiny config script
# instead, since it appears first.
import re
scripts = re.findall(r"<script.*?</script>", plotly_js, re.DOTALL)
plotly_js_tag = max(scripts, key=len) if scripts else ""

cp_prematch, cp_ht, cp_82 = D["checkpoints"]

result_banner = ""
if final_result:
    result_banner = f"""
    <div class="result-banner">
      <span class="tag">FULL TIME</span>
      <strong>{final_result['result']}</strong>
      <span class="detail">{final_result['winning_goal']['scorer']} {final_result['winning_goal']['minute']}
      &middot; {final_result['significance']}</span>
    </div>
    """

audit_section = ""
if audit and fig6:
    rows_html = "".join(f"""
      <tr>
        <td>{r['checkpoint']} ({r['score_at_checkpoint']})</td>
        <td>{r['predicted_spain_title_pct']:.1f}% / {r['predicted_argentina_title_pct']:.1f}%</td>
        <td>{r['winner_call']}</td>
        <td>{'Correct' if r['winner_call_correct'] else 'Wrong'}</td>
        <td>{r['brier_score']:.4f}</td>
      </tr>""" for r in audit["rows"])
    audit_section = f"""
    <section class="panel">
      <h2>Prediction performance audit</h2>
      <p class="note">Every checkpoint scored against the confirmed result. {audit['n_caveat']}</p>
      {fig_html(fig6, "audit-brier")}
      <table class="audit">
        <thead><tr><th>Checkpoint</th><th>Predicted Spain/Arg</th><th>Winner call</th>
        <th>Outcome</th><th>Brier score</th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
      <p class="note" style="margin-top:14px"><strong>Extra time call:</strong>
      predicted {audit['extra_time_call']['predicted_probability_at_min82_pct']}% at minute 82
      &rarr; {audit['extra_time_call']['actual']} (correct directional call).<br>
      <strong>Penalties call:</strong> predicted {audit['penalties_call']['predicted_probability_at_min82_pct']}%
      &rarr; {audit['penalties_call']['actual']}. {audit['penalties_call']['note']}<br>
      <strong>Scoreline:</strong> {audit['scoreline_check']['note']}<br>
      <strong>What the model could not see:</strong> {audit['not_modeled']['red_card']}</p>
    </section>
    """

elo_section = ""
if fig5:
    elo_section = f"""
    <section class="panel">
      <h2>Multi-horizon form trend</h2>
      <p class="note">World Football Elo rating for both finalists, counting back from
      match day. Use the range buttons above the chart — 7 days, 15 days, 1–16
      months, or the full 36-month window — to inspect any horizon, or drag the
      slider beneath the chart for a custom range.</p>
      {fig_html(fig5, "elo-trend")}
    </section>
    """
else:
    elo_section = """
    <section class="panel">
      <h2>Multi-horizon form trend</h2>
      <p class="note">Elo trend data pending — this panel populates once the
      historical-rating research completes.</p>
    </section>
    """

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>2026 World Cup Final — Spain vs Argentina: Interactive Forecast Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{plotly_js_tag}
<style>
  :root {{
    color-scheme: light;
    --surface-1: {SURFACE}; --page: #f9f9f7; --ink: {INK}; --ink2: {INK2};
    --muted: {MUTED}; --grid: {GRID}; --spain: {SPAIN}; --arg: {ARG};
    --border: rgba(11,11,11,0.10);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) {{
      color-scheme: dark;
      --surface-1: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7;
      --muted: #898781; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --surface-1: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--page); color: var(--ink);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 0 0 60px 0;
  }}
  header {{
    padding: 32px 24px 20px; max-width: 1180px; margin: 0 auto;
  }}
  header h1 {{ font-size: 1.65rem; margin: 0 0 6px; }}
  header p.sub {{ color: var(--ink2); margin: 0; font-size: 0.95rem; }}
  .kpi-row {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px; max-width: 1180px; margin: 20px auto; padding: 0 24px;
  }}
  .kpi {{
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 18px;
  }}
  .kpi .label {{ color: var(--ink2); font-size: 0.8rem; text-transform: uppercase;
    letter-spacing: 0.03em; margin-bottom: 8px; }}
  .kpi .row {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .kpi .team {{ font-size: 0.95rem; color: var(--ink2); }}
  .kpi .pct {{ font-size: 1.5rem; font-weight: 700; font-variant-numeric: tabular-nums; }}
  .kpi .spain {{ color: var(--spain); }}
  .kpi .arg {{ color: var(--arg); }}
  main {{ max-width: 1180px; margin: 0 auto; padding: 0 24px; }}
  section.panel {{
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px 22px 12px; margin-bottom: 22px;
  }}
  section.panel h2 {{ font-size: 1.15rem; margin: 0 0 6px; }}
  section.panel p.note {{ color: var(--ink2); font-size: 0.88rem; margin: 0 0 12px; max-width: 800px; }}
  .filter-row {{
    display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px;
  }}
  .filter-row button {{
    background: var(--page); border: 1px solid var(--grid); color: var(--ink);
    border-radius: 999px; padding: 6px 14px; font-size: 0.85rem; cursor: pointer;
  }}
  .filter-row button.active {{ background: var(--spain); color: white; border-color: var(--spain); }}
  table.audit {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  table.audit th, table.audit td {{ text-align: left; padding: 8px 10px;
    border-bottom: 1px solid var(--grid); }}
  table.audit th {{ color: var(--ink2); font-weight: 600; font-size: 0.8rem;
    text-transform: uppercase; letter-spacing: 0.02em; }}
  footer {{ max-width: 1180px; margin: 30px auto 0; padding: 0 24px; color: var(--ink2);
    font-size: 0.82rem; line-height: 1.6; }}
  footer a {{ color: var(--spain); }}
  .result-banner {{
    max-width: 1180px; margin: 0 auto 0; padding: 12px 24px;
    display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap;
  }}
  .result-banner .tag {{
    background: var(--spain); color: white; font-size: 0.72rem; font-weight: 700;
    padding: 3px 8px; border-radius: 4px; letter-spacing: 0.04em;
  }}
  .result-banner strong {{ font-size: 1.1rem; }}
  .result-banner .detail {{ color: var(--ink2); font-size: 0.88rem; }}
</style>
</head>
<body>
<header>
  <h1>2026 World Cup Final — Spain vs Argentina</h1>
  <p class="sub">Interactive forecast dashboard · MetLife Stadium, 19 July 2026 ·
  Market de-vigging + Elo + Opta ensemble → Dixon-Coles Monte Carlo, updated live at
  halftime and minute 82.</p>
</header>
{result_banner}
<div class="kpi-row">
  <div class="kpi">
    <div class="label">{cp_prematch['label']} ({cp_prematch['score_at_checkpoint']})</div>
    <div class="row"><span class="team spain">Spain</span><span class="pct spain">{cp_prematch['spain_title']*100:.1f}%</span></div>
    <div class="row"><span class="team arg">Argentina</span><span class="pct arg">{cp_prematch['argentina_title']*100:.1f}%</span></div>
  </div>
  <div class="kpi">
    <div class="label">{cp_ht['label']} ({cp_ht['score_at_checkpoint']})</div>
    <div class="row"><span class="team spain">Spain</span><span class="pct spain">{cp_ht['spain_title']*100:.1f}%</span></div>
    <div class="row"><span class="team arg">Argentina</span><span class="pct arg">{cp_ht['argentina_title']*100:.1f}%</span></div>
  </div>
  <div class="kpi">
    <div class="label">{cp_82['label']} ({cp_82['score_at_checkpoint']})</div>
    <div class="row"><span class="team spain">Spain</span><span class="pct spain">{cp_82['spain_title']*100:.1f}%</span></div>
    <div class="row"><span class="team arg">Argentina</span><span class="pct arg">{cp_82['argentina_title']*100:.1f}%</span></div>
  </div>
  <div class="kpi">
    <div class="label">Reaches a shootout (from min 82)</div>
    <div class="row"><span class="team">Probability</span><span class="pct" style="color:var(--ink)">{cp_82['reach_pens']*100:.1f}%</span></div>
    <div class="row"><span class="team" style="font-size:0.78rem">Argentina favored 58/42 in that scenario</span></div>
  </div>
</div>

<main>
  <section class="panel">
    <h2>Probability evolution</h2>
    <p class="note">How the title estimate moved as the match unfolded. Hover any point for
    the exact figure and checkpoint.</p>
    {fig_html(fig1, "prob-evo")}
  </section>

  <section class="panel">
    <h2>Path to the trophy</h2>
    <p class="note">Every route to lifting the cup, split by stage. Use the dropdown
    (top right of the chart) to filter by checkpoint.</p>
    {fig_html(fig2, "path-title")}
  </section>

  <section class="panel">
    <h2>Scoreline probability grid</h2>
    <p class="note">Full joint probability of each scoreline (Dixon-Coles-adjusted
    Poisson). Filter by checkpoint via the dropdown.</p>
    {fig_html(fig3, "scoreline-grid")}
  </section>

  <section class="panel">
    <h2>Where the estimate is fragile</h2>
    <p class="note">The minute-82 verdict hinges on one assumption: Argentina's
    penalty-shootout edge. This sweep shows exactly where the favorite flips.</p>
    {fig_html(fig4, "sensitivity")}
  </section>

  {elo_section}

  {audit_section}
</main>

<footer>
  Method: market de-vigging (proportional + power) · World Football Elo · Opta
  supercomputer ensemble · Dixon-Coles-adjusted Poisson score engine · 500,000-trial
  Monte Carlo with extra time and penalty shootout. Full methodology, verified sources,
  and reproducible code: <code>final-forecast/README.md</code> in the
  <strong>2026-Data-World-Champ</strong> repository. For entertainment and forecasting
  practice only — not betting advice.
</footer>
</body>
</html>
"""

out_path = os.path.join(HERE, "dashboard", "dashboard.html")
with open(out_path, "w") as f:
    f.write(html)

print("Wrote", out_path, f"({os.path.getsize(out_path)/1024:.0f} KB)")
