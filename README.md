# 2026-Data-World-Champ
### A data-driven champion forecast for the 2026 FIFA World Cup

A **rigorous, reproducible, quantitative** prediction of the 2026 FIFA World Cup
(Canada · Mexico · USA) — built as a transparent statistical pipeline, **not** an
opinion. Every number is reproduced by the code in [`src/`](src/) from grounded,
cited data.

> **Headline pick (consensus model): 🇪🇸 Spain**, narrowly over **France** and a
> market-defying **Argentina**. The *pure* statistical model actually makes
> **Argentina** its single most likely winner — a quantified, defensible
> disagreement with the betting market that independently matches Nate Silver's
> *PELE* model. **See the full analysis in [`REPORT.md`](REPORT.md).**

---

## 📊 The method in one line

**World Football Elo → calibrated Poisson goal model → exact Poisson-binomial
group stage → 200,000-simulation Monte-Carlo knockout**, with rating/form
uncertainty, host advantage, the official FIFA bracket, and the best-third-place
combination assignment — fully validated and seeded.

| Layer | Technique | Status |
|-------|-----------|--------|
| Ratings | World Football Elo (eloratings.net, Jun 2026) | grounded |
| Match outcome | Elo logistic → Skellam/Poisson, **calibrated to 0.4% error** | proven |
| Group stage | **Exact** Poisson-binomial + 3⁶ enumeration (= DFT = MC) | exact |
| Knockout | 200k Monte-Carlo over FIFA R32 bracket; 495 third-place patterns valid | simulated |
| Uncertainty | per-tournament form random effect (σ = 70 Elo) + MC standard errors | quantified |

---

## 🏆 Top of the board (consensus)

| # | Team | Model | Market | **Consensus** |
|--:|------|------:|-------:|--------------:|
| 1 | Spain | 21.1% | 14.2% | **18.4%** |
| 2 | France | 15.8% | 17.0% | **17.1%** |
| 3 | Argentina | 21.8% | 8.5% | **15.2%** |
| 4 | England | 7.6% | 10.6% | **9.2%** |
| 5 | Portugal | 4.6% | 9.5% | **6.7%** |

*Full 48-team forecast and the math behind it: **[`REPORT.md`](REPORT.md)**.*

---

## 📁 What's in this repo

```
data/
  teams_2026.csv              # 48 teams: group, Elo, FIFA pts, market odds, confederation
  bracket_structure.json      # official FIFA R32→Final bracket + 3rd-place eligibility
src/
  worldcup2026_model.py       # the engine: ratings→Poisson→Poisson-binomial→Monte-Carlo
  build_deliverables.py       # 6 figures + the Excel workbook
  build_report.py             # regenerates REPORT.md from the outputs
outputs/
  champion_probabilities.csv          # title odds, all 48
  group_stage_probabilities.csv       # win-group / advance, all 48
  technical_appendix_A_poisson_binomial.csv   # exact per-team PB distribution
  match_matrix_group.csv              # all 72 group fixtures: W/D/L + xG
  expected_score_matrix_48x48.csv     # full head-to-head matrix
  sensitivity_form_sd.csv, calibration.csv, forecast_full.csv
  figures/*.png                       # 6 publication-quality charts
  WorldCup2026_Forecast.xlsx          # ⭐ 8-sheet professional workbook
REPORT.md                     # the full analysis: proofs, calculations, references
```

### ⭐ The spreadsheet — `outputs/WorldCup2026_Forecast.xlsx`
Eight formatted, colour-scaled sheets with embedded charts: **Overview ·
Champion Forecast (48) · Group Stage · Appendix A (Poisson-Binomial) · Match
Matrix · Model vs Market · Sensitivity · Methodology & Sources.**

---

## ▶️ Reproduce everything
```bash
pip install numpy pandas scipy openpyxl matplotlib
python3 src/worldcup2026_model.py     # model + CSVs + self-validation  (~17 s)
python3 src/build_deliverables.py     # figures + Excel workbook
python3 src/build_report.py           # regenerates REPORT.md
```

---

## ✅ Why trust it (validation)
- **Poisson-binomial by convolution = by DFT** (max diff `0.0`) — implementation proof.
- **Goal model = Elo logistic** to a max error of **0.0040**.
- **Monte-Carlo = exact analytic** expected points (max diff < 0.02).
- **All 495** third-place qualification patterns produce a valid bracket assignment.
- Every probability distribution **sums to 1.000**; MC standard error ≈ 0.09 pp.
- Reproduces the market's elite-tier *size*, and the *PELE* model's Argentina↑/Portugal↓ tilts.

---

*Built as a benchmark of quantitative rigour (the development chain, proofs,
calculations, grounding and references) versus opinion-based forecasting. See the
`Kimi_Agent_World Cup 300-Agent Forecast/` directory for the qualitative-ensemble
foil this project is contrasted against.*
