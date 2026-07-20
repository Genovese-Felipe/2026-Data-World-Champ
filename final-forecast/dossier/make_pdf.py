#!/usr/bin/env python3
"""Prediction-performance PDF dossier -- reportlab Platypus, with the chart
PNGs embedded. Sober, professional layout: single accent color, typography
for hierarchy, no colored badges/pills per the repo's stated design
preferences (FGen-Labs CLAUDE.md owner preferences apply across this
session's deliverables)."""
import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, PageBreak, HRFlowable)
from reportlab.lib.enums import TA_LEFT

HERE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(HERE, "charts")
EXPORTS = os.path.join(HERE, "exports")

with open(os.path.join(HERE, "master_data.json")) as f:
    D = json.load(f)
with open(os.path.join(HERE, "final_result.json")) as f:
    FINAL = json.load(f)
with open(os.path.join(HERE, "audit.json")) as f:
    AUDIT = json.load(f)

NAVY = colors.HexColor("#0b0b0b")
BLUE = colors.HexColor("#2a78d6")
ORANGE = colors.HexColor("#eb6834")
GRAY = colors.HexColor("#52514e")
LIGHT = colors.HexColor("#f4f6f8")
GRID = colors.HexColor("#e1e0d9")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1", parent=styles["Title"], fontName="Helvetica-Bold",
                           fontSize=22, textColor=NAVY, spaceAfter=4))
styles.add(ParagraphStyle("H1Sub", parent=styles["Normal"], fontName="Helvetica",
                           fontSize=11, textColor=GRAY, spaceAfter=18))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                           fontSize=14, textColor=NAVY, spaceBefore=18, spaceAfter=8))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                           fontSize=9.5, textColor=NAVY, leading=14))
styles.add(ParagraphStyle("Note", parent=styles["Normal"], fontName="Helvetica-Oblique",
                           fontSize=8.5, textColor=GRAY, leading=12))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontName="Helvetica",
                           fontSize=8, textColor=GRAY, alignment=TA_LEFT, spaceBefore=4, spaceAfter=12))
styles.add(ParagraphStyle("ResultBanner", parent=styles["Normal"], fontName="Helvetica-Bold",
                           fontSize=13, textColor=BLUE, spaceAfter=2))

story = []

story.append(Paragraph("2026 FIFA World Cup Final", styles["H1"]))
story.append(Paragraph("Prediction-Performance Dossier &nbsp;&middot;&nbsp; Spain vs Argentina "
                        "&nbsp;&middot;&nbsp; MetLife Stadium &nbsp;&middot;&nbsp; 19 July 2026",
                        styles["H1Sub"]))
story.append(Paragraph(f"FULL TIME: {FINAL['result']}", styles["ResultBanner"]))
story.append(Paragraph(f"{FINAL['winning_goal']['scorer']} {FINAL['winning_goal']['minute']} — "
                        f"{FINAL['significance']}", styles["Body"]))
story.append(HRFlowable(width="100%", thickness=0.75, color=GRID, spaceBefore=10, spaceAfter=14))

# --- headline table ---
head_data = [["Checkpoint", "Match state", "Spain", "Argentina", "Winner call", "Result"]]
for r in AUDIT["rows"]:
    head_data.append([
        r["checkpoint"], r["score_at_checkpoint"],
        f"{r['predicted_spain_title_pct']:.1f}%", f"{r['predicted_argentina_title_pct']:.1f}%",
        r["winner_call"], "Correct" if r["winner_call_correct"] else "Wrong",
    ])
t = Table(head_data, colWidths=[1.0 * inch, 0.9 * inch, 0.75 * inch, 0.85 * inch, 0.95 * inch, 0.75 * inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.5, GRID),
    ("ALIGN", (2, 0), (-1, -1), "CENTER"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ("TEXTCOLOR", (2, 1), (2, -1), BLUE),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(t)
story.append(Spacer(1, 6))
story.append(Paragraph(AUDIT["n_caveat"], styles["Note"]))

story.append(PageBreak())

# --- method summary ---
story.append(Paragraph("Method", styles["H2"]))
story.append(Paragraph(
    "Market de-vigging (proportional + power method) on two independent odds sets "
    "(FanDuel/DraftKings/Oddschecker consensus and the Kalshi prediction-market "
    "contract) blended with World Football Elo and the Opta supercomputer's 25,000-"
    "simulation preview (weights 55/30/15). The blend calibrates a Dixon-Coles-"
    "adjusted Poisson score engine, run through a 500,000-trial Monte Carlo covering "
    "90 minutes, extra time at reduced intensity, and a penalty shootout. Two live "
    "updates re-ran the same engine conditioned on the actual match state: at "
    "halftime (0-0) and at minute 82 (still 0-0), the latter solved in closed form "
    "with an explicit sensitivity sweep on Argentina's shootout win probability — "
    "the single most decision-relevant assumption once the match reached that stage.",
    styles["Body"]))

for img, cap in [
    ("01_probability_evolution.png", "Figure 1. Championship probability at each forecast checkpoint."),
    ("05_funnel.png", "Figure 2. Chance the match reaches extra time, checkpoint by checkpoint."),
]:
    story.append(Spacer(1, 8))
    story.append(Image(os.path.join(CHARTS, img), width=6.3 * inch,
                        height=6.3 * inch * 0.58))
    story.append(Paragraph(cap, styles["Caption"]))

story.append(PageBreak())

story.append(Paragraph("Path to the trophy &amp; scoreline grid", styles["H2"]))
for img, cap in [
    ("02_path_to_title.png", "Figure 3. Title probability split by stage (regulation / extra time / penalties)."),
    ("03_scoreline_heatmap.png", "Figure 4. Pre-match scoreline probability grid (Dixon-Coles Poisson, 90 minutes)."),
]:
    story.append(Image(os.path.join(CHARTS, img), width=6.3 * inch,
                        height=6.3 * inch * (5.5 / 9 if "path" in img else 6.5 / 7.5)))
    story.append(Paragraph(cap, styles["Caption"]))
    story.append(Spacer(1, 6))

story.append(PageBreak())

story.append(Paragraph("Where the estimate was fragile", styles["H2"]))
story.append(Paragraph(
    "At minute 82 the entire verdict hinged on one number: Argentina's assumed "
    "penalty-shootout win probability. The sweep below shows exactly where the "
    "favorite flips (~63%). The central estimate (58%) kept Spain a narrow "
    "favorite; the match never tested this branch — it was decided by an extra-time "
    "goal before a shootout was needed.", styles["Body"]))
story.append(Image(os.path.join(CHARTS, "04_sensitivity_tornado.png"), width=6.3 * inch,
                    height=6.3 * inch * (5 / 12)))
story.append(Paragraph("Figure 5. Blend-weight sensitivity (left) and minute-82 shootout "
                        "sensitivity (right).", styles["Caption"]))

story.append(PageBreak())

story.append(Paragraph("36-month form trend", styles["H2"]))
story.append(Paragraph(
    "World Football Elo rating for both finalists, reconstructed from primary "
    "match-by-match data (eloratings.net). Both teams won their respective "
    "continental titles on the same day, 14 July 2024 — Spain (Euro 2024) and "
    "Argentina (Copa America 2024) — before converging on this final.", styles["Body"]))
story.append(Image(os.path.join(CHARTS, "06_elo_trend.png"), width=6.3 * inch,
                    height=6.3 * inch * (5.5 / 11)))
story.append(Paragraph("Figure 6. Elo trajectory, July 2023 to the final whistle.", styles["Caption"]))

story.append(PageBreak())

story.append(Paragraph("Prediction-performance audit", styles["H2"]))
story.append(Image(os.path.join(CHARTS, "07_audit_scorecard.png"), width=6.0 * inch,
                    height=6.0 * inch * (5 / 8.5)))
story.append(Paragraph("Figure 7. Brier score per checkpoint vs. the coin-flip baseline.",
                        styles["Caption"]))

story.append(Paragraph("Right, wrong, and untested", styles["H2"]))
audit_notes = [
    ("Right", "Favored Spain at all three checkpoints; Spain won."),
    ("Right", f"Assigned {AUDIT['extra_time_call']['predicted_probability_at_min82_pct']}% to extra time "
              "at minute 82; the match went to extra time."),
    ("Right", "0-0 was the model's highest-weight 90-minute scoreline by minute 82 — exactly the "
              "90-minute result."),
    ("Partially right", "1-0 was the model's #2 most likely 90-minute scoreline pre-match (12.5%) and "
                          "is the exact final score, but it arrived via extra time — a different "
                          "mechanism than the bucket it was priced under."),
    ("Untested, not wrong", "The shootout sensitivity sweep was the most decision-relevant analysis at "
                             "minute 82; the match never reached penalties, so that branch was never "
                             "tested against reality."),
    ("Blind spot", "Enzo Fernandez's red card came in stoppage time of regulation, after the minute-82 "
                    "checkpoint. The model had no live-card layer to react to it."),
    ("Next time", "Add a live-event layer (cards, dismissals, injuries) and run live updates every "
                   "10-15 minutes rather than at two fixed checkpoints."),
]
data = [["Verdict", "Note"]] + [[v, n] for v, n in audit_notes]
t2 = Table(data, colWidths=[1.3 * inch, 5.0 * inch])
verdict_style = [
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
    ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("GRID", (0, 0), (-1, -1), 0.5, GRID),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]
t2.setStyle(TableStyle(verdict_style))
story.append(t2)

story.append(Spacer(1, 16))
story.append(HRFlowable(width="100%", thickness=0.75, color=GRID, spaceBefore=6, spaceAfter=8))
story.append(Paragraph(
    "For entertainment and forecasting practice only — not betting advice. Full "
    "methodology, verified sources, and reproducible code: final-forecast/README.md "
    "in the 2026-Data-World-Champ repository.", styles["Note"]))

out_path = os.path.join(EXPORTS, "wc2026_final_prediction_dossier.pdf")
doc = SimpleDocTemplate(out_path, pagesize=letter,
                         leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                         topMargin=0.6 * inch, bottomMargin=0.6 * inch)
doc.build(story)
print("Wrote", out_path)
