#!/usr/bin/env python3
"""Runnable Dash app with real server-side Python callbacks -- the literal
"Plotly Python rendered in a web app page" version, for anyone who wants to
run it locally rather than view the static dashboard.html artifact (the
artifact is the one you can open immediately with no setup; this needs
`pip install dash` and a local Python process).

Run:
    pip install dash
    python3 dash_app.py
    # open http://127.0.0.1:8050
"""
import json
import os

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "master_data.json")) as f:
    D = json.load(f)
with open(os.path.join(HERE, "elo_trend.json")) as f:
    ELO = json.load(f)
with open(os.path.join(HERE, "final_result.json")) as f:
    FINAL = json.load(f)
with open(os.path.join(HERE, "audit.json")) as f:
    AUDIT = json.load(f)

SPAIN, ARG, MUTED, GRID, SURFACE = "#2a78d6", "#eb6834", "#898781", "#e1e0d9", "#fcfcfb"
LAYOUT = dict(paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, margin=dict(l=55, r=25, t=55, b=45))

app = dash.Dash(__name__, title="2026 World Cup Final -- Forecast Dashboard")
server = app.server

checkpoint_options = [{"label": c["label"], "value": i} for i, c in enumerate(D["checkpoints"])]


def path_figure(cp_idx):
    cp = D["checkpoints"][cp_idx]
    fig = go.Figure()
    for stage, alpha in [("regulation", 1.0), ("extra_time", 0.75), ("penalties", 0.4)]:
        fig.add_trace(go.Bar(
            x=["Spain", "Argentina"],
            y=[cp["path_spain"][stage] * 100, cp["path_argentina"][stage] * 100],
            name=stage.replace("_", " ").title(),
            marker_color=[f"rgba(42,120,214,{alpha})", f"rgba(235,104,52,{alpha})"],
        ))
    fig.update_layout(barmode="stack", title=f"Path to the trophy — {cp['label']}",
                       yaxis=dict(range=[0, 65], title="Title probability (%)"), **LAYOUT)
    return fig


def scoreline_figure(cp_idx):
    cp = D["checkpoints"][cp_idx]
    N = 5
    mat = [[0.0] * N for _ in range(N)]
    for k, v in cp["score_grid"].items():
        a, b = map(int, k.split("-"))
        if a < N and b < N:
            mat[a][b] = round(v * 100, 2)
    fig = go.Figure(go.Heatmap(z=mat, colorscale="Blues", text=[[f"{v:.1f}%" for v in row] for row in mat],
                                texttemplate="%{text}"))
    fig.update_layout(title=f"Scoreline grid — {cp['label']}",
                       xaxis_title="Argentina goals", yaxis_title="Spain goals", **LAYOUT)
    return fig


app.layout = html.Div(style={"fontFamily": "system-ui, sans-serif", "maxWidth": "1100px",
                              "margin": "0 auto", "padding": "24px"}, children=[
    html.H1("2026 World Cup Final — Spain vs Argentina", style={"marginBottom": "4px"}),
    html.P(f"FULL TIME: {FINAL['result']} — {FINAL['winning_goal']['scorer']} "
           f"{FINAL['winning_goal']['minute']}", style={"color": SPAIN, "fontWeight": "bold"}),
    html.Hr(style={"borderColor": GRID}),

    html.H2("Path to the trophy"),
    html.Label("Checkpoint:"),
    dcc.Dropdown(id="checkpoint-dropdown", options=checkpoint_options, value=2, clearable=False,
                 style={"width": "300px", "marginBottom": "12px"}),
    dcc.Graph(id="path-graph"),

    html.H2("Scoreline probability grid"),
    dcc.Graph(id="scoreline-graph"),

    html.H2("Elo trend — filter by lookback window"),
    dcc.RadioItems(
        id="elo-range",
        options=[{"label": l, "value": v} for l, v in
                 [("7d", 7), ("15d", 15), ("1m", 30), ("2m", 60), ("3m", 90), ("4m", 120),
                  ("6m", 180), ("9m", 270), ("12m", 365), ("16m", 487), ("All (36m)", 1100)]],
        value=1100, inline=True, style={"marginBottom": "12px"},
    ),
    dcc.Graph(id="elo-graph"),

    html.H2("Prediction audit"),
    dcc.Graph(
        figure=go.Figure(
            go.Bar(x=[r["checkpoint"] for r in AUDIT["rows"]],
                   y=[r["brier_score"] for r in AUDIT["rows"]],
                   marker_color=SPAIN, text=[f"{r['brier_score']:.4f}" for r in AUDIT["rows"]],
                   textposition="outside"),
        ).add_hline(y=0.25, line=dict(color=MUTED, dash="dash"),
                    annotation_text="coin-flip baseline")
        .update_layout(title="Brier score vs. coin-flip baseline", yaxis=dict(range=[0, 0.3]), **LAYOUT)
    ),
    html.P(AUDIT["n_caveat"], style={"color": MUTED, "fontSize": "0.85rem", "maxWidth": "700px"}),
])


@app.callback(Output("path-graph", "figure"), Input("checkpoint-dropdown", "value"))
def update_path(cp_idx):
    return path_figure(cp_idx)


@app.callback(Output("scoreline-graph", "figure"), Input("checkpoint-dropdown", "value"))
def update_scoreline(cp_idx):
    return scoreline_figure(cp_idx)


@app.callback(Output("elo-graph", "figure"), Input("elo-range", "value"))
def update_elo(days_back):
    import datetime
    cutoff = (datetime.date(2026, 7, 19) - datetime.timedelta(days=days_back)).isoformat()
    fig = go.Figure()
    for team, color, name in [("spain", SPAIN, "Spain"), ("argentina", ARG, "Argentina")]:
        pts = [p for p in ELO[team] if p["date"] >= cutoff]
        if not pts and ELO[team]:
            pts = [ELO[team][-1]]
        fig.add_trace(go.Scatter(x=[p["date"] for p in pts], y=[p["rating"] for p in pts],
                                  mode="lines+markers", name=name,
                                  line=dict(color=color, shape="hv"),
                                  text=[p["context"] for p in pts],
                                  hovertemplate="%{x}<br>Elo %{y}<br>%{text}<extra>" + name + "</extra>"))
    fig.update_layout(title=f"Elo rating — last {days_back} days", yaxis_title="Elo rating", **LAYOUT)
    return fig


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
