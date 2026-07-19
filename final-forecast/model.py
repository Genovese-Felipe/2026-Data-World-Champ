#!/usr/bin/env python3
"""Outcome-scenario model for the 2026 FIFA World Cup final: Spain vs Argentina.

Method (each step is a named, standard technique):

1. Market de-vigging. Bookmaker 1X2 odds contain an overround (the "vig").
   We strip it two ways -- proportional normalization and the power method --
   and average them. De-vigged closing odds are the best-calibrated public
   forecast of a football match (Strumbelj 2014, "On determining probability
   forecasts from betting odds").

2. Elo-based structural model. The World Football Elo rating difference maps
   to a win expectancy W = 1 / (1 + 10^(-d/400)). We convert that two-outcome
   expectancy into goal-rate parameters (see step 3) so the same engine
   produces scorelines, not just results.

3. Score engine: Dixon-Coles-adjusted Poisson. Team goal rates (lambda_s,
   lambda_a) are solved numerically so that (a) the implied 90-minute
   win/draw/win matches the target probabilities and (b) total expected goals
   matches the market total (from the over/under line). The Dixon-Coles tau
   correction (rho < 0) repairs the known Poisson bias on 0-0/1-0/0-1/1-1
   scores -- important in finals, which skew low-scoring.

4. Ensemble blend. Final 90-minute probabilities are a precision-weighted
   blend: de-vigged market average (weight 0.55), Elo structural model
   (0.15), published statistical models like Opta's supercomputer (0.30).
   Markets get the largest weight because they aggregate all other signals
   and are the best calibrated source; published models add independent
   information; raw Elo is the weakest single signal.

5. Monte Carlo tournament-of-one. 500,000 simulated finals: 90 minutes from
   the Dixon-Coles grid; if level, 30 minutes of extra time at reduced
   per-minute intensity (historical ET scoring runs ~0.85x regulation rate);
   if still level, a penalty shootout with an asymmetric win probability
   reflecting shootout-specific skill (goalkeeper record, conversion history).

6. Scenario sensitivity. The blend weights are perturbed (market-heavy /
   model-heavy) to produce a plausible range, not just a point estimate.

Run:  python3 model.py            (reads inputs.json, writes results.json)
"""

import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------------
# Step 1: de-vigging
# ----------------------------------------------------------------------------

def devig_proportional(odds):
    """Proportional (basic) normalization of decimal odds -> probabilities."""
    raw = [1.0 / o for o in odds]
    s = sum(raw)
    return [r / s for r in raw]


def devig_power(odds, tol=1e-12):
    """Power-method de-vig: find k so sum((1/o)^k) = 1. Better tail behavior."""
    raw = [1.0 / o for o in odds]
    lo, hi = 0.5, 3.0
    for _ in range(200):
        k = 0.5 * (lo + hi)
        s = sum(r ** k for r in raw)
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            lo = k
        else:
            hi = k
    return [r ** k for r in raw]


def devig(odds):
    p1 = devig_proportional(odds)
    p2 = devig_power(odds)
    return [(a + b) / 2.0 for a, b in zip(p1, p2)]


# ----------------------------------------------------------------------------
# Step 2/3: Elo -> goal rates -> Dixon-Coles score grid
# ----------------------------------------------------------------------------

MAX_GOALS = 10


def dc_tau(x, y, lam, mu, rho):
    """Dixon-Coles low-score correction factor."""
    if x == 0 and y == 0:
        return 1.0 - lam * mu * rho
    if x == 0 and y == 1:
        return 1.0 + lam * rho
    if x == 1 and y == 0:
        return 1.0 + mu * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def score_grid(lam, mu, rho):
    """Joint probability grid P(spain=x, argentina=y), DC-adjusted, normalized."""
    grid = {}
    total = 0.0
    for x in range(MAX_GOALS + 1):
        for y in range(MAX_GOALS + 1):
            p = poisson_pmf(x, lam) * poisson_pmf(y, mu) * dc_tau(x, y, lam, mu, rho)
            p = max(p, 0.0)
            grid[(x, y)] = p
            total += p
    return {k: v / total for k, v in grid.items()}


def grid_1x2(grid):
    ps = sum(v for (x, y), v in grid.items() if x > y)
    pd = sum(v for (x, y), v in grid.items() if x == y)
    pa = sum(v for (x, y), v in grid.items() if x < y)
    return ps, pd, pa


def solve_lambdas(target_ps, target_pa, total_goals, rho):
    """Find (lam, mu) s.t. the DC grid reproduces the target win probs and
    lam + mu = total_goals. Coordinate search on the win-prob gap."""
    lam = total_goals / 2.0
    for _ in range(80):
        mu = total_goals - lam
        ps, _, pa = grid_1x2(score_grid(lam, mu, rho))
        gap = (ps - pa) - (target_ps - target_pa)
        if abs(gap) < 1e-5:
            break
        lam -= gap * 0.35  # damped correction
        lam = min(max(lam, 0.05), total_goals - 0.05)
    return lam, total_goals - lam


def elo_1x2(elo_a, elo_b, draw_base=0.28):
    """Two-outcome Elo expectancy split into 1X2 with an empirical draw share.

    Draw probability shrinks as the rating gap grows (Davidson-style):
    p_draw = draw_base * exp(-(d/400)^2). Neutral venue, no home bonus.
    """
    d = elo_a - elo_b
    we = 1.0 / (1.0 + 10.0 ** (-d / 400.0))
    p_draw = draw_base * math.exp(-((d / 400.0) ** 2))
    p_a = we * (1.0 - p_draw)
    p_b = (1.0 - we) * (1.0 - p_draw)
    return p_a, p_draw, p_b


# ----------------------------------------------------------------------------
# Step 5: Monte Carlo
# ----------------------------------------------------------------------------

def sample_from_grid(grid, rng):
    r = rng.random()
    acc = 0.0
    for k, v in grid.items():
        acc += v
        if r <= acc:
            return k
    return (0, 0)


def simulate(n, grid90, lam, mu, rho, et_intensity, pen_win_spain, seed=20260719):
    rng = random.Random(seed)
    # extra-time grid: 30 minutes at reduced per-minute rate
    lam_et = lam * (30.0 / 90.0) * et_intensity
    mu_et = mu * (30.0 / 90.0) * et_intensity
    grid_et = score_grid(lam_et, mu_et, rho)

    counts = {
        "spain_90": 0, "draw_90": 0, "argentina_90": 0,
        "spain_et": 0, "argentina_et": 0,
        "spain_pens": 0, "argentina_pens": 0,
        "extra_time": 0, "penalties": 0,
        "btts": 0, "over25": 0, "over15": 0,
    }
    scores90 = {}
    for _ in range(n):
        s, a = sample_from_grid(grid90, rng)
        scores90[(s, a)] = scores90.get((s, a), 0) + 1
        if s > 0 and a > 0:
            counts["btts"] += 1
        if s + a > 2.5:
            counts["over25"] += 1
        if s + a > 1.5:
            counts["over15"] += 1
        if s > a:
            counts["spain_90"] += 1
            continue
        if a > s:
            counts["argentina_90"] += 1
            continue
        counts["draw_90"] += 1
        counts["extra_time"] += 1
        es, ea = sample_from_grid(grid_et, rng)
        if es > ea:
            counts["spain_et"] += 1
        elif ea > es:
            counts["argentina_et"] += 1
        else:
            counts["penalties"] += 1
            if rng.random() < pen_win_spain:
                counts["spain_pens"] += 1
            else:
                counts["argentina_pens"] += 1
    return counts, scores90


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def run(params):
    n = params["n_sims"]
    rho = params["dc_rho"]

    # --- market signal
    mo = params["market_odds_1x2"]  # [spain, draw, argentina] decimal
    p_market = devig(mo)

    # --- Elo signal
    p_elo = elo_1x2(params["elo_spain"], params["elo_argentina"],
                    params["draw_base"])

    # --- published models signal (already probabilities, may need renorm)
    pm = params["published_models_1x2"]  # list of [ps, pd, pa]
    if pm:
        avg = [sum(m[i] for m in pm) / len(pm) for i in range(3)]
        s = sum(avg)
        p_pub = [x / s for x in avg]
    else:
        p_pub = None

    # --- blend
    w = params["blend_weights"]  # {market, elo, published}
    signals = [(p_market, w["market"]), (list(p_elo), w["elo"])]
    if p_pub:
        signals.append((p_pub, w["published"]))
    tw = sum(wt for _, wt in signals)
    blend = [sum(p[i] * wt for p, wt in signals) / tw for i in range(3)]

    # --- market total goals from O/U (approx: line +/- price skew)
    total = params["expected_total_goals"]

    lam, mu = solve_lambdas(blend[0], blend[2], total, rho)
    grid90 = score_grid(lam, mu, rho)
    counts, scores90 = simulate(
        n, grid90, lam, mu, rho,
        params["et_intensity"], params["pen_win_spain"])

    def pct(k):
        return counts[k] / n

    spain_title = pct("spain_90") + pct("spain_et") + pct("spain_pens")
    arg_title = pct("argentina_90") + pct("argentina_et") + pct("argentina_pens")

    top_scores = sorted(scores90.items(), key=lambda kv: -kv[1])[:10]

    results = {
        "inputs_summary": {
            "market_devig_1x2": [round(x, 4) for x in p_market],
            "elo_1x2": [round(x, 4) for x in p_elo],
            "published_avg_1x2": [round(x, 4) for x in p_pub] if p_pub else None,
            "blended_1x2": [round(x, 4) for x in blend],
            "lambda_spain": round(lam, 3),
            "lambda_argentina": round(mu, 3),
        },
        "ninety_minutes": {
            "spain_win": round(pct("spain_90"), 4),
            "draw": round(pct("draw_90"), 4),
            "argentina_win": round(pct("argentina_90"), 4),
        },
        "path_to_title": {
            "spain_in_90": round(pct("spain_90"), 4),
            "spain_in_extra_time": round(pct("spain_et"), 4),
            "spain_on_penalties": round(pct("spain_pens"), 4),
            "argentina_in_90": round(pct("argentina_90"), 4),
            "argentina_in_extra_time": round(pct("argentina_et"), 4),
            "argentina_on_penalties": round(pct("argentina_pens"), 4),
        },
        "championship": {
            "spain_lifts_trophy": round(spain_title, 4),
            "argentina_lifts_trophy": round(arg_title, 4),
        },
        "match_shape": {
            "goes_to_extra_time": round(pct("extra_time"), 4),
            "goes_to_penalties": round(pct("penalties"), 4),
            "both_teams_score_90": round(pct("btts"), 4),
            "over_1_5_goals_90": round(pct("over15"), 4),
            "over_2_5_goals_90": round(pct("over25"), 4),
        },
        "most_likely_scorelines_90": [
            {"score": f"{s}-{a} (Spain-Argentina)", "prob": round(c / n, 4)}
            for (s, a), c in top_scores
        ],
    }
    return results


def main():
    with open(os.path.join(HERE, "inputs.json")) as f:
        params = json.load(f)

    results = {"base_case": run(params)}

    # scenario sensitivity: market-heavy vs model-heavy blends
    for name, weights in params["scenarios"].items():
        p2 = dict(params)
        p2["blend_weights"] = weights
        results[name] = run(p2)

    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(results, f, indent=2)

    b = results["base_case"]
    print("=== 2026 World Cup final: Spain vs Argentina ===")
    print(f"Blended 90-min probabilities: {b['inputs_summary']['blended_1x2']}")
    print(f"Championship: Spain {b['championship']['spain_lifts_trophy']:.1%}, "
          f"Argentina {b['championship']['argentina_lifts_trophy']:.1%}")
    print(f"Extra time: {b['match_shape']['goes_to_extra_time']:.1%}, "
          f"Penalties: {b['match_shape']['goes_to_penalties']:.1%}")
    print("Top scorelines (90 min):")
    for row in b["most_likely_scorelines_90"][:6]:
        print(f"  {row['score']}: {row['prob']:.1%}")


if __name__ == "__main__":
    main()
