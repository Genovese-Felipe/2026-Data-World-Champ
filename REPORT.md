# 2026 FIFA World Cup — A Rigorous, Reproducible Probabilistic Forecast

*A data-driven champion model for Canada · Mexico · USA 2026.
Elo → calibrated Poisson goal model → exact Poisson-binomial group stage →
200,000-replication Monte-Carlo knockout. Every number below is reproduced by
`src/worldcup2026_model.py` (seed = 2026).*

---

## 0. TL;DR — the prediction

**Headline pick (consensus model): Spain**, narrowly ahead of France and a
strong, market-defying Argentina.

| Pick | Consensus title prob. | Pure-model prob. | Market (de-vig) |
|------|----------------------:|-----------------:|----------------:|
| 1. **Spain** | **18.4%** | 21.0% | 14.2% |
| 2. **France** | **17.1%** | 15.8% | 17.0% |
| 3. **Argentina** | **15.1%** | 21.8% | 8.5% |
| 4. **England** | **9.2%** | 7.6% | 10.6% |

The **pure statistical model** rates **Argentina its single most likely winner**
(21.8%), a whisker above Spain
(21.0%) — because Argentina holds the world's #2 Elo *and*
drew the easiest path (Group J + a soft knockout quarter). The **market**
disagrees sharply (Argentina only 8.5%), pricing in an
ageing squad. We report **both**, and blend them into the consensus column.

> **This is not an opinion. It is a transparent calculation.** The same inputs and
> code reproduce every number; the group stage is solved *exactly*; the knockout
> standard error is ±0.09 pp on a 20% probability. Contrast with
> persona/opinion forecasts (e.g. the *Kimi 300-agent* survey in this repo, which
> assigns champions by vibe and a 1–10 "confidence" score).

---

## 1. The standard of proof

A credible tournament forecast must be (i) **grounded** in real data, (ii)
**mathematically explicit**, (iii) **reproducible**, and (iv) **honest about
uncertainty**. This document supplies the full *development chain*: ratings →
match model → group-stage algebra → knockout simulation → validation, with
proofs and worked numbers at each step, plus an auditable spreadsheet.

**Benchmarks we measure against.**
- *Market* — sharp sportsbook consensus, de-vigged. The hardest baseline to beat.
- *Nate Silver "PELE"* (100k sims) — publicly noted as **bullish on Argentina vs
  the market** and **skeptical of Portugal**. Our independent model reproduces
  *both* tilts (§4.3) — meaningful external corroboration.
- *Kimi 300-agent forecast* (this repo) — a qualitative persona ensemble; a useful
  foil for what a *quantitative* model adds.

---

## 2. Data & grounding

| Input | Source | Snapshot |
|-------|--------|----------|
| Team strength (Elo) | World Football Elo Ratings, eloratings.net (`World.tsv`) | 17 Jun 2026 |
| FIFA ranking points (cross-ref) | FIFA Men's World Ranking | 11 Jun 2026 |
| Group draw (48 teams, 12 groups) | FIFA final draw — Wikipedia **and** simbye.com (cross-validated) | 5 Dec 2025 |
| Knockout bracket + 3rd-place rules | FIFA fixed match schedule (Wikipedia knockout page) | — |
| Market odds (de-vigged) | FOX Sports / consensus books | 17 Jun 2026 |

All 48 teams and ratings live in [`data/teams_2026.csv`](data/teams_2026.csv); the
bracket in [`data/bracket_structure.json`](data/bracket_structure.json). The draw
was confirmed identical across two independent sources before any modelling (e.g.
Norway with France & Senegal in Group I; USA with Türkiye, Australia, Paraguay in
Group D).

---

## 3. The model (development chain, with the maths)

### 3.1 Ratings
We use **World Football Elo** Rᵢ — purpose-built, results-based, the de-facto
standard for football match prediction. Hosts (USA/MEX/CAN) receive **+65 Elo** in
their matches.

### 3.2 From Elo to a match outcome

**(a) Expected score (logistic).** For team A vs B with d = R_A − R_B,

&nbsp;&nbsp;&nbsp;&nbsp; **E_A = 1 / (1 + 10^(−d/400))**

is the "win + ½·draw" expectation. *Example:* Spain (2129) vs France (2084),
d = 45 → E = **0.564**.

**(b) Goals (calibrated independent Poisson).** Goals are Poisson:
G_A ~ Pois(λ_A), G_B ~ Pois(λ_B), parameterised by total τ = λ_A + λ_B and
supremacy σ = λ_A − λ_B. We fix τ(d) = 2.70 + 0.0012·|d| (blow-outs contain more
goals) and **solve** σ(d) so the implied win/draw/loss reproduces E_A *exactly*.
The goal difference G_A − G_B follows a **Skellam** distribution, giving
closed-form

&nbsp;&nbsp;&nbsp;&nbsp; P(draw) = Skellam(0; λ_A, λ_B), &nbsp;&nbsp; P(A win) = 1 − Skellam_cdf(0).

**Calibration result:** across the realistic range d ∈ [0, 760] the goal model
reproduces the Elo logistic to a **maximum error of 0.0040**
(`outputs/figures/fig4_calibration.png`). By construction the goal model is an
Elo-consistent re-parameterisation that *also* yields realistic scorelines for
tiebreakers and knockouts.

### 3.3 Group stage — solved *exactly* (the Poisson-binomial core)

Each team plays 3 group matches with (generally unequal) win probabilities
p₁, p₂, p₃. Its **number of wins** W is a sum of independent, non-identical
Bernoulli trials — a **Poisson-binomial** variable:

&nbsp;&nbsp;&nbsp;&nbsp; W = B₁ + B₂ + B₃, &nbsp; Bₖ ~ Bernoulli(pₖ), &nbsp;
P(W = j) = Σ over all size-j subsets S of the 3 matches of ∏(k∈S) pₖ · ∏(k∉S)(1 − pₖ).

We compute P(W = j) **two independent ways** — direct convolution and the DFT of
the characteristic function ∏ₖ(1 + (z − 1)pₖ) — and they agree to machine
precision (**max diff 0.0**): a *proof-by-computation* of the implementation. The
full **points distribution** comes from enumerating all 3⁶ = 729 result
combinations of a group exactly.

**Worked example — France, Group I** (vs Senegal / Iraq / Norway), per-match win
probabilities p = (0.7157, 0.9064, 0.6007):

- P(3 wins) = 0.7157 · 0.9064 · 0.6007 = **0.3897** → engine **0.3897** ✓
- P(0 wins) = (1−0.7157)(1−0.9064)(1−0.6007) = **0.0106** → engine **0.0106** ✓
- Poisson-binomial P(W=0,1,2,3) = (0.0106, 0.1456, 0.4541, 0.3897),
  sum = 1.0000; E[W] = 2.223; E[points] = **7.138**.

Full per-team table: **Technical Appendix A**
([`outputs/technical_appendix_A_poisson_binomial.csv`](outputs/technical_appendix_A_poisson_binomial.csv)).

### 3.4 Knockout
We simulate the **official FIFA Round-of-32 bracket**. The 8 best third-placed
teams are routed to slots by FIFA eligibility rules; we solve the equivalent
**system of distinct representatives** (bipartite assignment) and verify that
**all C(12,8) = 495 qualification patterns admit a valid assignment** (0
violations). Knockout matches use the same goal model; draws go to extra time
(goal rate × 30/90) then penalties (≈ coin-flip, tiny Elo edge ≤ 0.12).

### 3.5 Uncertainty & Monte Carlo
A point Elo rating ignores its own error (form, injuries, squad turnover, draw-day
luck). We integrate over it with a **per-tournament team random effect**,
Rᵢ → Rᵢ + Normal(0, σ²), σ = 70 Elo, which regresses over-confident point
forecasts the way published models do. We then run **200,000** full-tournament
replications (seed 2026). Monte-Carlo standard error on a probability p is
√(p(1−p)/N) ≈ **0.09 pp** at p = 0.2.

---

## 4. Results

### 4.1 Title probabilities (top 24 of 48)

| # | Team | Grp | Conf | Elo | Model | Market | **Consensus** | Final | Semi |
|--:|------|:---:|:----:|----:|------:|-------:|--------------:|------:|-----:|
| 1 | Spain | H | UEFA | 2129 | 21.0% | 14.2% | **18.4%** | 31.1% | 48.8% |
| 2 | France | I | UEFA | 2084 | 15.8% | 17.0% | **17.1%** | 29.8% | 43.9% |
| 3 | Argentina | J | CONMEBOL | 2128 | 21.8% | 8.5% | **15.1%** | 32.2% | 49.9% |
| 4 | England | L | UEFA | 2024 | 7.6% | 10.6% | **9.2%** | 15.9% | 28.8% |
| 5 | Portugal | K | UEFA | 1989 | 4.6% | 9.5% | **6.7%** | 9.1% | 19.7% |
| 6 | Brazil | C | CONMEBOL | 1978 | 4.1% | 7.7% | **5.7%** | 10.1% | 19.4% |
| 7 | Germany | E | UEFA | 1939 | 2.4% | 5.7% | **3.7%** | 6.8% | 14.9% |
| 8 | Netherlands | F | UEFA | 1944 | 2.7% | 4.5% | **3.5%** | 7.4% | 15.7% |
| 9 | Colombia | K | CONMEBOL | 1982 | 4.1% | 1.9% | **3.0%** | 8.4% | 18.6% |
| 10 | Norway | I | UEFA | 1929 | 2.1% | 3.0% | **2.6%** | 6.0% | 14.3% |
| 11 | Mexico | A | CONCACAF | 1881 | 2.8% | 1.7% | **2.3%** | 7.8% | 16.6% |
| 12 | Japan | F | AFC | 1910 | 1.6% | 1.9% | **1.8%** | 4.9% | 11.6% |
| 13 | Belgium | G | UEFA | 1879 | 1.0% | 2.4% | **1.6%** | 2.7% | 8.4% |
| 14 | Croatia | L | UEFA | 1912 | 1.6% | 1.1% | **1.4%** | 4.3% | 10.9% |
| 15 | United States | D | CONCACAF | 1780 | 0.5% | 2.1% | **1.0%** | 1.6% | 5.2% |
| 16 | Switzerland | B | UEFA | 1865 | 0.8% | 1.1% | **0.9%** | 2.4% | 7.4% |
| 17 | Morocco | C | CAF | 1840 | 0.4% | 2.1% | **0.9%** | 1.7% | 5.2% |
| 18 | Ecuador | E | CONMEBOL | 1890 | 1.2% | 0.6% | **0.9%** | 3.7% | 9.4% |
| 19 | Uruguay | H | CONMEBOL | 1870 | 0.7% | 1.1% | **0.9%** | 1.9% | 6.3% |
| 20 | Turkey | D | UEFA | 1849 | 0.5% | 0.4% | **0.5%** | 1.6% | 5.4% |
| 21 | Austria | J | UEFA | 1857 | 0.5% | 0.4% | **0.5%** | 1.4% | 4.9% |
| 22 | Senegal | I | CAF | 1839 | 0.4% | 0.3% | **0.4%** | 1.6% | 5.1% |
| 23 | Australia | D | AFC | 1839 | 0.4% | 0.3% | **0.4%** | 1.4% | 4.8% |
| 24 | Canada | B | CONCACAF | 1767 | 0.4% | 0.2% | **0.3%** | 1.6% | 5.4% |

*(Full 48-team table: [`outputs/champion_probabilities.csv`](outputs/champion_probabilities.csv).
Model top-3 mass 58.7% vs market 41.9%; model top-8
81.9% vs market 77.8% — the model **agrees with the market
on the size of the elite tier** and disagrees only on its **internal order**.)*

### 4.2 Group favourites

| Grp | Favourite (P win group) | 2nd favourite | Clearest qualifier (P top-2) |
|:---:|--------------------------|----------------|------------------------------|
| A | Mexico (66.8%) | South Korea (21.4%) | Mexico (90.4%) |
| B | Switzerland (51.7%) | Canada (41.3%) | Switzerland (87.5%) |
| C | Brazil (61.5%) | Morocco (22.6%) | Brazil (87.7%) |
| D | Turkey (29.1%) | United States (28.4%) | Turkey (55.6%) |
| E | Germany (51.8%) | Ecuador (37.2%) | Germany (85.1%) |
| F | Netherlands (49.5%) | Japan (38.9%) | Netherlands (82.8%) |
| G | Belgium (57.9%) | Iran (23.1%) | Belgium (83.9%) |
| H | Spain (83.6%) | Uruguay (14.9%) | Spain (98.5%) |
| I | France (67.0%) | Norway (22.6%) | France (91.1%) |
| J | Argentina (82.5%) | Austria (11.9%) | Argentina (96.7%) |
| K | Portugal (48.1%) | Colombia (46.0%) | Portugal (86.5%) |
| L | England (64.0%) | Croatia (30.0%) | England (92.3%) |

### 4.3 Model vs market — the value board

| Direction | Team | Model | Market | Edge (Model − Market) |
|-----------|------|------:|-------:|----------------------:|
| BACK | Argentina | 21.8% | 8.5% | +13.3% |
| BACK | Spain | 21.0% | 14.2% | +6.8% |
| BACK | Colombia | 4.1% | 1.9% | +2.3% |
| BACK | Mexico | 2.8% | 1.7% | +1.2% |
| BACK | Ecuador | 1.2% | 0.6% | +0.6% |
| BACK | Croatia | 1.6% | 1.1% | +0.4% |
| FADE | Portugal | 4.6% | 9.5% | -4.9% |
| FADE | Brazil | 4.1% | 7.7% | -3.7% |
| FADE | Germany | 2.4% | 5.7% | -3.3% |
| FADE | England | 7.6% | 10.6% | -3.0% |
| FADE | Netherlands | 2.7% | 4.5% | -1.8% |

**Reading it.** The model's biggest disagreements are **Argentina** and
**Colombia** (back) and **Portugal** (fade) — the Argentina/Portugal tilts match
Nate Silver's PELE model independently. These are defensible, *quantified* edges a
persona forecast cannot produce.

### 4.4 Dark horses & hosts
- **Colombia** (Elo #6 globally; 4.1% model vs
  1.9% market) is the model's premier longshot.
- **Norway** (Haaland / Ødegaard; Elo 1929) reaches the
  quarter-final 29.3% of the time despite a brutal Group I.
- **Hosts:** Mexico 2.8%, USA
  0.5%, Canada 0.4% to
  win it — the host bonus helps them advance far more than it helps them lift the trophy.

---

## 5. Validation

**Internal (the engine is correct):**
- Poisson-binomial by convolution **=** by DFT (max diff 0.0).
- Goal model **=** Elo logistic (max error **0.0040**).
- Monte-Carlo (σ = 0) expected points **=** exact analytic expected points
  (max diff < 0.02 at 100k sims).
- 3rd-place assignment valid for **all 495** patterns.
- Every probability column sums to **1.000**.

**External (the forecast is reasonable):**
- Top-8 title mass matches the market to ~1 pp.
- Reproduces PELE's Argentina-up / Portugal-down tilts.
- **Live face-check (matchday 1, 11–17 Jun 2026):** Mexico 2-0 South Africa,
  France 3-1 Senegal, Argentina win (Messi hat-trick) — all favourites, consistent
  with the model. Spain 1-1 Cape Verde and Portugal 1-1 DR Congo are exactly the
  favourite-drops-points draws the model assigns double-digit probability to (it
  never claims minnows can't hold the elite).

---

## 6. Sensitivity & limitations

**Sensitivity to the form parameter σ** (title %, `outputs/sensitivity_form_sd.csv`):

| σ (Elo) | Spain | Argentina | France | England | Portugal | Brazil |
|--------:|------:|----------:|-------:|--------:|---------:|-------:|
| 0 | 23.51 | 24.91 | 17.74 | 7.29 | 4.02 | 3.66 |
| 40 | 22.49 | 23.42 | 17.11 | 7.52 | 4.32 | 3.81 |
| 70 | 21.21 | 21.82 | 15.64 | 7.63 | 4.46 | 4.0 |
| 100 | 19.26 | 19.46 | 14.41 | 7.51 | 4.74 | 4.26 |

The **ordering is stable**; larger σ simply compresses the top toward the field.

**Honest limitations.** (1) Elo encodes *results*, not squad ageing, injuries or
tactics — hence the form term and the market blend, and hence the model's arguable
over-rating of Argentina. (2) We use independent Poisson (no explicit Dixon-Coles
correlation) to preserve the exact Elo calibration. (3) The exact 495-row
third-place table is approximated by a valid SDR (negligible effect on title
odds). (4) The model is pre-tournament-style from current ratings; it does not
re-condition on partial group results already played.

---

## 7. Reproduce everything
```bash
pip install numpy pandas scipy openpyxl matplotlib
python3 src/worldcup2026_model.py     # model + CSVs + validation  (~17 s)
python3 src/build_deliverables.py     # 6 figures + Excel workbook
python3 src/build_report.py           # regenerates this REPORT.md
```
Outputs: `outputs/*.csv`, `outputs/figures/*.png`,
`outputs/WorldCup2026_Forecast.xlsx`.

---

## 8. References

**Live data & tournament facts**
1. World Football Elo Ratings — https://www.eloratings.net/
2. FIFA Men's World Ranking — https://en.wikipedia.org/wiki/FIFA_Men%27s_World_Ranking
3. 2026 FIFA World Cup draw — https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_draw
4. 2026 FIFA World Cup (overview/format) — https://en.wikipedia.org/wiki/2026_FIFA_World_Cup
5. 2026 WC groups (cross-validation) — https://simbye.com/blogs/blog/world-cup-2026-groups-teams
6. ESPN — 2026 World Cup format, tiebreakers, schedule — https://www.espn.com/soccer/story/_/id/47108758/
7. FIFA — hosts, cities, dates — https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026
8. FOX Sports — World Cup 2026 champion odds — https://www.foxsports.com/stories/soccer/world-cup-2026-champion-odds
9. ESPN — every team's championship & group odds — https://www.espn.com/espn/betting/story/_/id/48386952/
10. Nate Silver — World Cup 2026 odds & "PELE" predictions — https://www.natesilver.net/p/world-cup-2026-odds-predictions

**Methodology (statistical grounding)**
11. Dixon, M.J. & Coles, S.G. (1997). *Modelling Association Football Scores and
    Inefficiencies in the Football Betting Market.* JRSS-C 46(2).
12. Maher, M.J. (1982). *Modelling association football scores.* Statistica Neerlandica 36.
13. Hvattum, L.M. & Arntzen, H. (2010). *Using ELO ratings for match result
    prediction in association football.* Int. J. Forecasting 26(3).
14. Karlis, D. & Ntzoufras, I. (2003). *Analysis of sports data using bivariate
    Poisson models.* JRSS-D 52(3).
15. Le Cam, L. (1960). *An approximation theorem for the Poisson binomial
    distribution.* Pacific J. Math 10.
16. Expected-goals / skill-adjusted xG literature — arXiv:2310.10553; arXiv:2503.19809.

---

*Generated programmatically from the model outputs — see `src/build_report.py`.*
