# Forecast dossier — Spain vs Argentina, 2026 World Cup final

Everything in this folder was generated after the match finished
(**Spain 1-0 Argentina, AET**), consolidating the three live forecast
checkpoints from `../model.py`, `../live_min82.py`, and the confirmed
result into one set of visual and exportable deliverables.

## What's here

| File / folder | What it is | How to open |
|---|---|---|
| `dashboard/dashboard.html` | Self-contained interactive Plotly dashboard — probability evolution, path-to-title, scoreline grid, sensitivity sweep, 36-month Elo trend with range filters, and the prediction audit | Open directly in any browser, no server needed |
| `dash_app.py` | The same dashboard as a real Dash app with server-side Python callbacks | `pip install dash && python3 dash_app.py`, then open `http://127.0.0.1:8050` |
| `charts/` | 7 static PNG charts (probability evolution, path-to-title, scoreline heatmap, sensitivity tornado, funnel, Elo trend, audit scorecard) + `probability_evolution.gif` | Any image viewer |
| `exports/wc2026_final_prediction_dossier.xlsx` | Formatted workbook: summary, per-checkpoint detail, inputs & sources, 36-month Elo trend, right/wrong notes — with live formulas | Excel, LibreOffice, Google Sheets |
| `exports/wc2026_final_prediction_dossier.pdf` | The same content as a polished, print-ready report | Any PDF reader |
| `master_data.json`, `elo_trend.json`, `final_result.json`, `audit.json` | The underlying data every chart/export reads from — single source of truth | — |
| `data_prep.py`, `make_charts.py`, `make_charts2.py`, `make_animation.py`, `make_dashboard.py`, `make_xlsx.py`, `make_pdf.py` | The scripts that build everything above, in dependency order | `python3 <script>.py` |

## Reproducing

```bash
cd final-forecast/dossier
python3 data_prep.py       # consolidates model.py + live_min82.py output
python3 make_audit.py      # scores checkpoints against final_result.json
python3 make_charts.py     # static charts 01-05
python3 make_charts2.py    # Elo trend + audit scorecard (06-07)
python3 make_animation.py  # GIF
python3 make_dashboard.py  # dashboard.html
python3 make_xlsx.py       # XLSX (then recalc with LibreOffice, see below)
python3 make_pdf.py        # PDF
```

Recalculate the XLSX's live formulas (openpyxl writes formulas without
cached values):
```bash
python3 /root/.claude/skills/xlsx/scripts/recalc.py exports/wc2026_final_prediction_dossier.xlsx 300
```
If you skip this step, the formulas are still valid Excel/LibreOffice/Sheets
formulas and will compute correctly the moment you open the file in any of
those — the recalc step only matters for *programmatic* readers that load
cached values without opening a real spreadsheet engine first.

## On "video"

There is no AI video-generation tool available in this session (no
Sora/Veo-class connector was connected). `probability_evolution.gif` is a
genuine data-driven animation — a matplotlib animation of the real
probability trajectory, smoothly interpolated between the three checkpoints
— not a rendered/narrated video. An MP4 export was attempted but `ffmpeg`
could not be installed in this environment (package-mirror errors); the GIF
is the full deliverable for the "animation" request.

## On the "last 7 days / 15 days / ... / 16 months, every 4 months" request

Read as a request for a multi-horizon historical trend (the interpretation
that maps to real, sourced data) rather than a recurring-service schedule,
since this is a single, already-completed match. The Elo trend panel in the
dashboard and `elo_trend.json` implement exactly those lookback windows —
7d, 15d, 1-16 months, then every 4 months back to 36 months — using Plotly's
native range-selector buttons. If a recurring analytics *service* (e.g. for
future tournaments) was actually intended, this pipeline (`model.py` +
`live_min82.py` + the `dossier/` scripts) is already structured to be rerun
on a schedule; ask and a Routine can be set up for that.

## Data integrity note

One correction was applied during assembly: a research pass initially
labeled Argentina's 11 July 2026 quarterfinal opponent as "Chile." This
session's earlier, adversarially-verified tournament-path research (cross-
checked against FIFA.com, Sky Sports, and Al Jazeera live blogs) confirms
the actual opponent was **Switzerland** (3-1 AET). The Elo rating *value* at
that date was unaffected — only the opponent label was wrong — and has been
corrected in `elo_trend.json` before it reached any chart or export.
