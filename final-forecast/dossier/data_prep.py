#!/usr/bin/env python3
"""Consolidates every number produced across the forecasting session into one
JSON payload that all downstream deliverables (charts, GIF, dashboard, XLSX,
PDF) read from. Single source of truth -- nothing here is re-derived
independently in each output format.

Checkpoints (all Spain vs Argentina, 2026 World Cup final, MetLife Stadium):
  1. Pre-match       -- before kickoff, market + Elo + Opta ensemble
  2. Halftime         -- 0-0 at the break, live-conditioned update
  3. Minute 82        -- still 0-0, closed-form update with shootout sweep
  4. Final (pending)  -- filled in once the research agent confirms the result

Run after final_result.json exists (written once the live/final result is
confirmed) or with FINAL_UNKNOWN=True to proceed without it.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FF = os.path.dirname(HERE)  # final-forecast/

with open(os.path.join(FF, "results.json")) as f:
    RESULTS = json.load(f)

with open(os.path.join(FF, "inputs.json")) as f:
    INPUTS = json.load(f)


def poisson(k, mu):
    return math.exp(-mu) * mu ** k / math.factorial(k)


def dc_tau(x, y, lam, mu, rho):
    if x == 0 and y == 0:
        return 1.0 - lam * mu * rho
    if x == 0 and y == 1:
        return 1.0 + lam * rho
    if x == 1 and y == 0:
        return 1.0 + mu * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def score_grid(lam, mu, rho, max_g=6):
    grid = {}
    total = 0.0
    for x in range(max_g + 1):
        for y in range(max_g + 1):
            p = max(poisson(x, lam) * poisson(y, mu) * dc_tau(x, y, lam, mu, rho), 0.0)
            grid[(x, y)] = p
            total += p
    return {k: v / total for k, v in grid.items()}


# ---------------------------------------------------------------------------
# Checkpoint 1: pre-match
# ---------------------------------------------------------------------------
pre = RESULTS["base_case_prematch"]
lam0, mu0 = pre["inputs_summary"]["lambda_spain"], pre["inputs_summary"]["lambda_argentina"]
grid_prematch = score_grid(lam0, mu0, INPUTS["dc_rho"])

checkpoint_prematch = {
    "label": "Pre-match",
    "minute": 0,
    "score_at_checkpoint": "0-0 (not started)",
    "spain_90": pre["ninety_minutes"]["spain_win"],
    "draw_90": pre["ninety_minutes"]["draw"],
    "argentina_90": pre["ninety_minutes"]["argentina_win"],
    "spain_title": pre["championship"]["spain_lifts_trophy"],
    "argentina_title": pre["championship"]["argentina_lifts_trophy"],
    "reach_et": pre["match_shape"]["goes_to_extra_time"],
    "reach_pens": pre["match_shape"]["goes_to_penalties"],
    "path_spain": {
        "regulation": pre["path_to_title"]["spain_in_90"],
        "extra_time": pre["path_to_title"]["spain_in_extra_time"],
        "penalties": pre["path_to_title"]["spain_on_penalties"],
    },
    "path_argentina": {
        "regulation": pre["path_to_title"]["argentina_in_90"],
        "extra_time": pre["path_to_title"]["argentina_in_extra_time"],
        "penalties": pre["path_to_title"]["argentina_on_penalties"],
    },
    "top_scorelines": pre["most_likely_scorelines_90"],
    "score_grid": {f"{k[0]}-{k[1]}": v for k, v in grid_prematch.items()},
    "signals": pre["inputs_summary"],
}

# ---------------------------------------------------------------------------
# Checkpoint 2: halftime (0-0)
# ---------------------------------------------------------------------------
ht = RESULTS["live_update_halftime_0_0"]
lam_ht = INPUTS["live_halftime"]
lam2h = lam0 * lam_ht["second_half_share"] * lam_ht["caginess_deflator"] * lam_ht["spain_adjust"]
mu2h = mu0 * lam_ht["second_half_share"] * lam_ht["caginess_deflator"] * lam_ht["argentina_adjust"]
grid_halftime = score_grid(lam2h, mu2h, INPUTS["dc_rho"])

checkpoint_halftime = {
    "label": "Halftime",
    "minute": 45,
    "score_at_checkpoint": "0-0",
    "spain_90": ht["ninety_minutes_from_here"]["spain_win"],
    "draw_90": ht["ninety_minutes_from_here"]["draw_level_after_90"],
    "argentina_90": ht["ninety_minutes_from_here"]["argentina_win"],
    "spain_title": ht["championship"]["spain_lifts_trophy"],
    "argentina_title": ht["championship"]["argentina_lifts_trophy"],
    "reach_et": ht["match_shape"]["goes_to_extra_time"],
    "reach_pens": ht["match_shape"]["goes_to_penalties"],
    "path_spain": {
        "regulation": ht["path_to_title"]["spain_in_90"],
        "extra_time": ht["path_to_title"]["spain_in_extra_time"],
        "penalties": ht["path_to_title"]["spain_on_penalties"],
    },
    "path_argentina": {
        "regulation": ht["path_to_title"]["argentina_in_90"],
        "extra_time": ht["path_to_title"]["argentina_in_extra_time"],
        "penalties": ht["path_to_title"]["argentina_on_penalties"],
    },
    "top_scorelines": ht["most_likely_final_scores_90"],
    "score_grid": {f"{k[0]}-{k[1]}": v for k, v in grid_halftime.items()},
}

# ---------------------------------------------------------------------------
# Checkpoint 3: minute 82 (0-0), closed-form with shootout sweep
# ---------------------------------------------------------------------------
MIN_LEFT = 12.0
MU_ESP_REG = 1.252 * (MIN_LEFT / 90.0) * 1.00
MU_ARG_REG = 0.948 * (MIN_LEFT / 90.0) * 0.72
MU_ESP_ET = 1.252 * (30.0 / 90.0) * 0.72
MU_ARG_ET = 0.948 * (30.0 / 90.0) * 0.72 * 0.85
PEN_ARG_CENTRAL = 0.58
PEN_SWEEP = [0.50, 0.55, 0.58, 0.60, 0.65]


def segment_outcome(mu_a, mu_b, kmax=10):
    pa = pb = pd = 0.0
    for a in range(kmax + 1):
        for b in range(kmax + 1):
            p = poisson(a, mu_a) * poisson(b, mu_b)
            if a > b:
                pa += p
            elif a < b:
                pb += p
            else:
                pd += p
    return pa, pd, pb


def title_probs(pen_arg):
    esp_reg, draw_reg, arg_reg = segment_outcome(MU_ESP_REG, MU_ARG_REG)
    esp_et, draw_et, arg_et = segment_outcome(MU_ESP_ET, MU_ARG_ET)
    reach_et = draw_reg
    reach_pens = reach_et * draw_et
    esp = esp_reg + reach_et * esp_et + reach_pens * (1 - pen_arg)
    arg = arg_reg + reach_et * arg_et + reach_pens * pen_arg
    return {
        "esp_reg": esp_reg, "arg_reg": arg_reg, "draw_reg": draw_reg,
        "esp_et": reach_et * esp_et, "arg_et": reach_et * arg_et,
        "esp_pen": reach_pens * (1 - pen_arg), "arg_pen": reach_pens * pen_arg,
        "reach_et": reach_et, "reach_pens": reach_pens,
        "esp_title": esp, "arg_title": arg,
    }


min82_central = title_probs(PEN_ARG_CENTRAL)
min82_sweep = [{"pen_arg": p, **title_probs(p)} for p in PEN_SWEEP]
grid_min82 = score_grid(MU_ESP_REG, MU_ARG_REG, INPUTS["dc_rho"], max_g=4)

checkpoint_min82 = {
    "label": "Minute 82",
    "minute": 82,
    "score_at_checkpoint": "0-0",
    "spain_90": min82_central["esp_reg"],  # win probability in remaining regulation only
    "draw_90": min82_central["reach_et"],
    "argentina_90": min82_central["arg_reg"],
    "spain_title": min82_central["esp_title"],
    "argentina_title": min82_central["arg_title"],
    "reach_et": min82_central["reach_et"],
    "reach_pens": min82_central["reach_pens"],
    "path_spain": {
        "regulation": min82_central["esp_reg"],
        "extra_time": min82_central["esp_et"],
        "penalties": min82_central["esp_pen"],
    },
    "path_argentina": {
        "regulation": min82_central["arg_reg"],
        "extra_time": min82_central["arg_et"],
        "penalties": min82_central["arg_pen"],
    },
    "penalty_sensitivity": min82_sweep,
    "score_grid": {f"{k[0]}-{k[1]}": v for k, v in grid_min82.items()},
}

# ---------------------------------------------------------------------------
# Scenario sensitivity (pre-match blend-weight stress test)
# ---------------------------------------------------------------------------
scenarios = {
    "base_case": {
        "label": "Base case (market 55 / published 30 / Elo 15)",
        "spain_title": RESULTS["base_case_prematch"]["championship"]["spain_lifts_trophy"],
        "argentina_title": RESULTS["base_case_prematch"]["championship"]["argentina_lifts_trophy"],
    },
    "scenario_market_heavy": {
        "label": "Market-heavy (market 80 / published 15 / Elo 5)",
        "spain_title": RESULTS["scenario_market_heavy"]["championship"]["spain_lifts_trophy"],
        "argentina_title": RESULTS["scenario_market_heavy"]["championship"]["argentina_lifts_trophy"],
    },
    "scenario_model_heavy": {
        "label": "Model-heavy (market 30 / published 40 / Elo 30)",
        "spain_title": RESULTS["scenario_model_heavy"]["championship"]["spain_lifts_trophy"],
        "argentina_title": RESULTS["scenario_model_heavy"]["championship"]["argentina_lifts_trophy"],
    },
}

payload = {
    "checkpoints": [checkpoint_prematch, checkpoint_halftime, checkpoint_min82],
    "scenarios": scenarios,
    "final_result": None,  # filled in by merge_final_result.py once known
}

with open(os.path.join(HERE, "master_data.json"), "w") as f:
    json.dump(payload, f, indent=2)

print("Wrote master_data.json")
print(f"Pre-match: Spain {checkpoint_prematch['spain_title']:.1%} / "
      f"Argentina {checkpoint_prematch['argentina_title']:.1%}")
print(f"Halftime:  Spain {checkpoint_halftime['spain_title']:.1%} / "
      f"Argentina {checkpoint_halftime['argentina_title']:.1%}")
print(f"Min 82:    Spain {checkpoint_min82['spain_title']:.1%} / "
      f"Argentina {checkpoint_min82['argentina_title']:.1%}")
