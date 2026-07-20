#!/usr/bin/env python3
"""Prediction-performance XLSX dossier. Per the xlsx skill: professional
font, formulas (not hardcoded results) wherever a value is derived from
other cells, hardcoded inputs documented with their source.
"""
import json
import os

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORTS = os.path.join(HERE, "exports")
os.makedirs(EXPORTS, exist_ok=True)

with open(os.path.join(HERE, "master_data.json")) as f:
    D = json.load(f)
with open(os.path.join(HERE, "final_result.json")) as f:
    FINAL = json.load(f)
with open(os.path.join(HERE, "audit.json")) as f:
    AUDIT = json.load(f)
with open(os.path.join(HERE, "elo_trend.json")) as f:
    ELO = json.load(f)
with open(os.path.join(os.path.dirname(HERE), "inputs.json")) as f:
    INPUTS = json.load(f)

FONT = "Arial"
NAVY = "1F2937"
BLUE = "2A78D6"
ORANGE = "EB6834"
LIGHT = "F4F6F8"
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
INPUT_FONT = Font(name=FONT, color="0000FF", size=10)
FORMULA_FONT = Font(name=FONT, color="000000", size=10)
HEADER_FONT = Font(name=FONT, color="FFFFFF", size=10, bold=True)
TITLE_FONT = Font(name=FONT, size=14, bold=True, color=NAVY)
NOTE_FONT = Font(name=FONT, size=9, italic=True, color="666666")
thin = Side(style="thin", color="D9D9D9")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)


def style_header_row(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def autosize(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


wb = Workbook()

# =====================================================================
# Sheet 1: Summary
# =====================================================================
ws = wb.active
ws.title = "Summary"
ws["B2"] = "2026 FIFA World Cup Final — Prediction-Performance Dossier"
ws["B2"].font = TITLE_FONT
ws["B3"] = "Spain vs Argentina · MetLife Stadium · 19 July 2026"
ws["B3"].font = Font(name=FONT, size=11, color="666666")

ws["B5"] = "Final result:"
ws["B5"].font = Font(name=FONT, bold=True)
ws["C5"] = FINAL["result"]
ws["C5"].font = Font(name=FONT, bold=True, color=BLUE)
ws["B6"] = "Winning goal:"
ws["C6"] = f"{FINAL['winning_goal']['scorer']}, {FINAL['winning_goal']['minute']}"
ws["B7"] = "Significance:"
ws["C7"] = FINAL["significance"]
ws["C7"].alignment = Alignment(wrap_text=True)
ws.row_dimensions[7].height = 30

headers = ["Checkpoint", "Match state", "Spain title %", "Argentina title %",
           "Winner call", "Outcome", "Brier score"]
hr = 10
for i, h in enumerate(headers, start=2):
    ws.cell(row=hr, column=i, value=h)
style_header_row(ws, hr, len(headers) + 1)

for i, r in enumerate(AUDIT["rows"]):
    row = hr + 1 + i
    ws.cell(row=row, column=2, value=r["checkpoint"]).font = FORMULA_FONT
    ws.cell(row=row, column=3, value=r["score_at_checkpoint"]).font = FORMULA_FONT
    c_spain = ws.cell(row=row, column=4, value=r["predicted_spain_title_pct"] / 100)
    c_spain.number_format = "0.0%"
    c_spain.font = INPUT_FONT
    c_arg = ws.cell(row=row, column=5, value=f"=1-{get_column_letter(4)}{row}")
    ws.cell(row=row, column=5).number_format = "0.0%"
    ws.cell(row=row, column=5).font = FORMULA_FONT
    ws.cell(row=row, column=6,
            value=f'=IF({get_column_letter(4)}{row}>0.5,"Spain","Argentina")').font = FORMULA_FONT
    ws.cell(row=row, column=7, value="Correct" if r["winner_call_correct"] else "Wrong").font = FORMULA_FONT
    c_brier = ws.cell(row=row, column=8, value=f"=({get_column_letter(4)}{row}-1)^2")
    c_brier.number_format = "0.0000"
    c_brier.font = FORMULA_FONT
    for c in range(2, 9):
        ws.cell(row=row, column=c).border = BORDER

baseline_row = hr + 1 + len(AUDIT["rows"]) + 1
ws.cell(row=baseline_row, column=2, value="Coin-flip baseline").font = Font(name=FONT, italic=True)
ws.cell(row=baseline_row, column=8, value=0.25).font = Font(name=FONT, italic=True, color="666666")
ws.cell(row=baseline_row, column=8).number_format = "0.0000"

note_row = baseline_row + 2
ws.cell(row=note_row, column=2, value="Note:").font = Font(name=FONT, bold=True, size=9)
ws.cell(row=note_row, column=3, value=AUDIT["n_caveat"]).font = NOTE_FONT
ws.cell(row=note_row, column=3).alignment = Alignment(wrap_text=True)
ws.merge_cells(start_row=note_row, start_column=3, end_row=note_row, end_column=8)
ws.row_dimensions[note_row].height = 45

autosize(ws, [3, 16, 14, 13, 15, 12, 10, 11])

# =====================================================================
# Sheet 2: Checkpoints (full detail)
# =====================================================================
ws2 = wb.create_sheet("Checkpoints")
ws2["B2"] = "Forecast detail by checkpoint"
ws2["B2"].font = TITLE_FONT

cols = ["Metric"] + [c["label"] for c in D["checkpoints"]]
hr2 = 4
for i, h in enumerate(cols, start=2):
    ws2.cell(row=hr2, column=i, value=h)
style_header_row(ws2, hr2, len(cols) + 1)

metrics = [
    ("Score at checkpoint", "score_at_checkpoint", None),
    ("Spain 90-min win %", "spain_90", 0.01),
    ("Draw / still-level %", "draw_90", 0.01),
    ("Argentina 90-min win %", "argentina_90", 0.01),
    ("Reaches extra time %", "reach_et", 0.01),
    ("Reaches penalties %", "reach_pens", 0.01),
    ("Spain: title via regulation %", "path_spain.regulation", 0.01),
    ("Spain: title via extra time %", "path_spain.extra_time", 0.01),
    ("Spain: title via penalties %", "path_spain.penalties", 0.01),
    ("Argentina: title via regulation %", "path_argentina.regulation", 0.01),
    ("Argentina: title via extra time %", "path_argentina.extra_time", 0.01),
    ("Argentina: title via penalties %", "path_argentina.penalties", 0.01),
    ("SPAIN TITLE PROBABILITY %", "spain_title", 0.01),
    ("ARGENTINA TITLE PROBABILITY %", "argentina_title", 0.01),
]


def get_nested(d, path):
    cur = d
    for part in path.split("."):
        cur = cur[part]
    return cur


for mi, (label, key, is_pct) in enumerate(metrics):
    row = hr2 + 1 + mi
    bold = key in ("spain_title", "argentina_title")
    lc = ws2.cell(row=row, column=2, value=label)
    lc.font = Font(name=FONT, bold=bold, size=10)
    for ci, cp in enumerate(D["checkpoints"]):
        val = get_nested(cp, key)
        cell = ws2.cell(row=row, column=3 + ci, value=val)
        if is_pct:
            cell.number_format = "0.0%"
        cell.font = Font(name=FONT, bold=bold, size=10,
                          color=BLUE if bold else "000000")
        cell.border = BORDER
    lc.border = BORDER

autosize(ws2, [3, 34, 16, 16, 16])

# =====================================================================
# Sheet 3: Inputs & sources
# =====================================================================
ws3 = wb.create_sheet("Inputs & Sources")
ws3["B2"] = "Model inputs (verified against primary sources)"
ws3["B2"].font = TITLE_FONT
ws3["B3"] = "Blue = hardcoded input. See notes column for source."
ws3["B3"].font = NOTE_FONT

input_rows = [
    ("Market odds set 1 (Spain/Draw/Arg, decimal)", str(INPUTS["market_odds_sets"][0]),
     "FanDuel closing line, cross-checked vs DraftKings & Oddschecker"),
    ("Market odds set 2 (Kalshi, decimal)", str(INPUTS["market_odds_sets"][1]),
     "Kalshi 3-way regulation contract"),
    ("Elo — Spain (pre-match)", INPUTS["elo_spain"], "eloratings.net, verified 2026-07-19 pre-kickoff"),
    ("Elo — Argentina (pre-match)", INPUTS["elo_argentina"], "eloratings.net, verified 2026-07-19 pre-kickoff"),
    ("Elo — Spain (post-final)", ELO["spain"][-1]["rating"], "eloratings.net, post-match update"),
    ("Elo — Argentina (post-final)", ELO["argentina"][-1]["rating"], "eloratings.net, post-match update"),
    ("Opta supercomputer 90-min (S/D/A)", str(INPUTS["published_models_1x2"][0]),
     "theanalyst.com, 25,000-sim preview, published match day"),
    ("Blend weights (market/published/Elo)",
     f"{INPUTS['blend_weights']['market']}/{INPUTS['blend_weights']['published']}/{INPUTS['blend_weights']['elo']}",
     "Weighted by demonstrated forecast calibration"),
    ("Expected total goals (pre-match)", INPUTS["expected_total_goals"], "Kalshi total-goals contract"),
    ("Dixon-Coles rho", INPUTS["dc_rho"], "Standard low-score correlation for international football"),
    ("Extra-time intensity multiplier", INPUTS["et_intensity"], "Historical ET scoring rate vs regulation"),
    ("Argentina penalty win probability (central)", 0.58,
     "Conservative read of Argentina's 6/7 WC shootout record + Dibu Martinez"),
]
hr3 = 5
headers3 = ["Input", "Value", "Source / note"]
for i, h in enumerate(headers3, start=2):
    ws3.cell(row=hr3, column=i, value=h)
style_header_row(ws3, hr3, 4)
for i, (label, val, note) in enumerate(input_rows):
    row = hr3 + 1 + i
    ws3.cell(row=row, column=2, value=label).font = Font(name=FONT, size=10)
    vcell = ws3.cell(row=row, column=3, value=val)
    vcell.font = INPUT_FONT
    ncell = ws3.cell(row=row, column=4, value=note)
    ncell.font = Font(name=FONT, size=9, color="444444")
    ncell.alignment = Alignment(wrap_text=True)
    for c in range(2, 5):
        ws3.cell(row=row, column=c).border = BORDER
autosize(ws3, [3, 38, 20, 55])

# =====================================================================
# Sheet 4: Elo trend
# =====================================================================
ws4 = wb.create_sheet("Elo Trend (36mo)")
ws4["B2"] = "World Football Elo rating history — Spain vs Argentina"
ws4["B2"].font = TITLE_FONT
ws4["B3"] = ELO["_methodology"]
ws4["B3"].font = NOTE_FONT
ws4["B3"].alignment = Alignment(wrap_text=True)
ws4.merge_cells("B3:F3")
ws4.row_dimensions[3].height = 60

hr4 = 6
headers4 = ["Date", "Spain Elo", "Spain context", "Argentina Elo", "Argentina context"]
for i, h in enumerate(headers4, start=2):
    ws4.cell(row=hr4, column=i, value=h)
style_header_row(ws4, hr4, 6)

all_dates = sorted(set([p["date"] for p in ELO["spain"]] + [p["date"] for p in ELO["argentina"]]))
sp_by_date = {p["date"]: p for p in ELO["spain"]}
ar_by_date = {p["date"]: p for p in ELO["argentina"]}
for i, dt in enumerate(all_dates):
    row = hr4 + 1 + i
    ws4.cell(row=row, column=2, value=dt).font = Font(name=FONT, size=10)
    sp = sp_by_date.get(dt)
    ar = ar_by_date.get(dt)
    ws4.cell(row=row, column=3, value=sp["rating"] if sp else None).font = INPUT_FONT
    ws4.cell(row=row, column=4, value=sp["context"] if sp else "").font = Font(name=FONT, size=9, color="444444")
    ws4.cell(row=row, column=5, value=ar["rating"] if ar else None).font = INPUT_FONT
    ws4.cell(row=row, column=6, value=ar["context"] if ar else "").font = Font(name=FONT, size=9, color="444444")
    for c in range(2, 7):
        ws4.cell(row=row, column=c).border = BORDER
autosize(ws4, [3, 12, 11, 34, 11, 34])

# =====================================================================
# Sheet 5: What we got right / wrong (narrative)
# =====================================================================
ws5 = wb.create_sheet("Right vs Wrong")
ws5["B2"] = "Notes for next time"
ws5["B2"].font = TITLE_FONT

notes = [
    ("RIGHT", "Winner call", "Favored Spain at all three checkpoints (57.8% / 54.7% / 52.7%); Spain won."),
    ("RIGHT", "Extra time", f"Assigned {AUDIT['extra_time_call']['predicted_probability_at_min82_pct']}% to reaching extra time at minute 82; match went to extra time."),
    ("RIGHT", "Scoreline shape", "0-0 was correctly the highest-weight 90-minute scoreline by minute 82; that is exactly the 90-minute result."),
    ("RIGHT", "Low-scoring final", "Pre-match model priced a low-scoring, cagey final (2.2 expected goals); final score after 90 was 0-0, decided 1-0 in ET."),
    ("PARTIALLY RIGHT", "Final scoreline", "1-0 was the model's #2 most likely 90-minute scoreline pre-match (12.5%) and is the exact final score — but it arrived via extra time, a different mechanism than the 90-minute bucket it was priced under."),
    ("UNTESTED, NOT WRONG", "Penalty shootout sensitivity", "Spent significant analysis on the shootout win-probability assumption (the single most decision-relevant lever at minute 82); the match never reached penalties, so that branch was never tested against reality."),
    ("BLIND SPOT", "Red card timing", "Enzo Fernandez's dismissal came in stoppage time of regulation, AFTER the minute-82 checkpoint. The model had no mechanism to react to live cards/dismissals -- a real gap, not a calculation error."),
    ("UNDERESTIMATE", "Shot dominance", "Modeled Argentina's attack at a flat 0.72x discount from minute 82; final shots were Spain 20-2 (12-0 on target), a larger gap than modeled, partly explained by the red card."),
    ("METHOD NOTE", "n=1 caveat", "A single match cannot validate calibration. Beating the coin-flip Brier baseline on the realized outcome is a reasonable-call signal, not proof of good calibration -- that requires many repeated trials."),
    ("NEXT TIME", "Live event layer", "Add a live-conditioning layer that reacts to cards, red cards, and injuries in real time, not just the scoreline, so in-play updates reflect personnel changes as they happen rather than only at fixed checkpoints."),
    ("NEXT TIME", "Denser live checkpoints", "Run the live update every ~10-15 minutes rather than at two fixed points (halftime, minute 82), so red cards / injuries this close to full time get priced in immediately."),
]
hr5 = 4
headers5 = ["Verdict", "Topic", "Detail"]
for i, h in enumerate(headers5, start=2):
    ws5.cell(row=hr5, column=i, value=h)
style_header_row(ws5, hr5, 4)

verdict_colors = {"RIGHT": "1B8A3A", "PARTIALLY RIGHT": "8A7A1B", "UNTESTED, NOT WRONG": "666666",
                   "BLIND SPOT": "C0392B", "UNDERESTIMATE": "C0392B", "METHOD NOTE": "666666",
                   "NEXT TIME": BLUE}
for i, (verdict, topic, detail) in enumerate(notes):
    row = hr5 + 1 + i
    vc = ws5.cell(row=row, column=2, value=verdict)
    vc.font = Font(name=FONT, bold=True, size=9.5, color=verdict_colors.get(verdict, "000000"))
    ws5.cell(row=row, column=3, value=topic).font = Font(name=FONT, bold=True, size=10)
    dc = ws5.cell(row=row, column=4, value=detail)
    dc.alignment = Alignment(wrap_text=True)
    dc.font = Font(name=FONT, size=9.5)
    ws5.row_dimensions[row].height = 44
    for c in range(2, 5):
        ws5.cell(row=row, column=c).border = BORDER
autosize(ws5, [3, 18, 20, 90])

out_path = os.path.join(EXPORTS, "wc2026_final_prediction_dossier.xlsx")
wb.save(out_path)
print("Wrote", out_path)
