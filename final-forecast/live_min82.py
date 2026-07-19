#!/usr/bin/env python3
"""Minute-82 live update for the 2026 World Cup final: Spain 0-0 Argentina.

Closed-form (exact) version of the base model's decision tree, conditioned on
the verified live state at ~82:00 — score level, ~12 minutes of regulation
left (8 + ~4 stoppage), Spain territorially dominant but scoreless, Argentina
producing zero shots.

Why closed-form instead of Monte Carlo here: with the game reduced to three
short independent Poisson segments (remaining regulation, extra time, then a
shootout Bernoulli), the tree is small enough to integrate exactly. No
simulation noise.

The decisive lever is the shootout win probability. Argentina owns the best
World Cup shootout record in history (6 of 7) and Emiliano Martinez is the
premier shootout goalkeeper of the era; Spain has lost 4 of its 5 (including
0-3 vs Morocco in 2022). But empirically, shootout skill edges are modest —
even elite keepers rarely push a shootout past ~58-60%. So rather than commit
to one number, we sweep the Argentina penalty-win probability and report how
the title verdict moves. Central estimate: 0.58.
"""
import math

# Remaining-regulation goal expectations over the last ~12 minutes.
# Pre-match blended rates were Spain 1.252 / Argentina 0.948 goals per 90.
# Spain held near baseline (territorial dominance offsets the compact block and
# the poor MetLife pitch); Argentina discounted for generating nothing and now
# defending for penalties.
MIN_LEFT = 12.0
MU_ESP_REG = 1.252 * (MIN_LEFT / 90.0) * 1.00   # 0.167
MU_ARG_REG = 0.948 * (MIN_LEFT / 90.0) * 0.72   # 0.091

# Extra time (30 min): reduced intensity for a cagey final, with an extra
# fatigue discount on Argentina (two extra-time matches already, one fewer
# rest day).
MU_ESP_ET = 1.252 * (30.0 / 90.0) * 0.72         # 0.300
MU_ARG_ET = 0.948 * (30.0 / 90.0) * 0.72 * 0.85  # 0.228

PEN_ARG_SWEEP = [0.50, 0.55, 0.58, 0.60, 0.65]
PEN_ARG_CENTRAL = 0.58


def poisson(k, mu):
    return math.exp(-mu) * mu ** k / math.factorial(k)


def segment_outcome(mu_a, mu_b, kmax=10):
    """From a level score, probability side A wins / draws / B wins this
    segment (A scores strictly more / equal / fewer)."""
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
    # remaining regulation
    esp_reg, draw_reg, arg_reg = segment_outcome(MU_ESP_REG, MU_ARG_REG)
    # extra time (conditional on reaching it)
    esp_et, draw_et, arg_et = segment_outcome(MU_ESP_ET, MU_ARG_ET)

    reach_et = draw_reg
    reach_pens = reach_et * draw_et

    esp = (esp_reg
           + reach_et * esp_et
           + reach_pens * (1 - pen_arg))
    arg = (arg_reg
           + reach_et * arg_et
           + reach_pens * pen_arg)
    return {
        "esp_reg": esp_reg, "arg_reg": arg_reg, "draw_reg": draw_reg,
        "esp_et": reach_et * esp_et, "arg_et": reach_et * arg_et,
        "esp_pen": reach_pens * (1 - pen_arg), "arg_pen": reach_pens * pen_arg,
        "reach_et": reach_et, "reach_pens": reach_pens,
        "esp_title": esp, "arg_title": arg,
    }


def main():
    print("=== Minute 82 live update: Spain 0-0 Argentina ===\n")
    print(f"Remaining-regulation goal expectation: Spain {MU_ESP_REG:.3f}, "
          f"Argentina {MU_ARG_REG:.3f}")
    print(f"Extra-time goal expectation:          Spain {MU_ESP_ET:.3f}, "
          f"Argentina {MU_ARG_ET:.3f}\n")

    c = title_probs(PEN_ARG_CENTRAL)
    print(f"Match still level at 90' (-> extra time): {c['reach_et']:.1%}")
    print(f"  Spain wins in remaining regulation:    {c['esp_reg']:.1%}")
    print(f"  Argentina wins in remaining regulation:{c['arg_reg']:.1%}")
    print(f"Reaches a penalty shootout:              {c['reach_pens']:.1%}\n")

    print("Central estimate (Argentina shootout edge = 58%):")
    print(f"  SPAIN to lift the trophy:     {c['esp_title']:.1%}")
    print(f"  ARGENTINA to lift the trophy: {c['arg_title']:.1%}")
    print(f"    Spain path:     reg {c['esp_reg']:.1%} | ET {c['esp_et']:.1%} "
          f"| pens {c['esp_pen']:.1%}")
    print(f"    Argentina path: reg {c['arg_reg']:.1%} | ET {c['arg_et']:.1%} "
          f"| pens {c['arg_pen']:.1%}\n")

    print("Sensitivity to the shootout assumption (the pivotal lever):")
    print(f"  {'Arg pen win%':>12} | {'Spain title':>11} | "
          f"{'Arg title':>10} | favorite")
    for pa in PEN_ARG_SWEEP:
        t = title_probs(pa)
        fav = "Spain" if t["esp_title"] > t["arg_title"] else "Argentina"
        print(f"  {pa:>11.0%} | {t['esp_title']:>10.1%} | "
              f"{t['arg_title']:>9.1%} | {fav}")


if __name__ == "__main__":
    main()
