#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 2026 FIFA WORLD CUP — QUANTITATIVE FORECAST ENGINE
================================================================================
A fully reproducible probabilistic model for the 2026 FIFA World Cup
(48 teams, 12 groups, Round of 32 knockout) built on:

   World Football Elo  --(logistic)-->  expected match score
                        --(calibrated)-> independent-Poisson goal model
                        --(Skellam)----> Win / Draw / Loss probabilities
   Group stage   : EXACT Poisson-binomial / 3^6 enumeration  (analytic)
   Knockout      : vectorised Monte-Carlo over the official bracket
                   + FIFA best-third-place combination assignment

Author: Claude (claude-opus-4-8) for the 2026-Data-World-Champ project.
Run:    python3 src/worldcup2026_model.py
Output: outputs/*.csv , outputs/figures/*.png , outputs/WorldCup2026_Forecast.xlsx

Every numeric constant below is documented; the model is deterministic given
the random seed.  See REPORT.md for the full mathematical development.
================================================================================
"""

import json, itertools, math, os
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.stats import skellam, poisson
from scipy.optimize import brentq, linear_sum_assignment

# --------------------------------------------------------------------------- #
# 0.  CONFIGURATION / CONSTANTS  (all documented)
# --------------------------------------------------------------------------- #
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA      = os.path.join(ROOT, "data")
OUT       = os.path.join(ROOT, "outputs")
FIG       = os.path.join(OUT, "figures")
os.makedirs(FIG, exist_ok=True)

SEED      = 2026
N_SIMS    = 200_000        # Monte-Carlo tournament replications
ELO_DIV   = 400.0          # Elo logistic divisor (standard)
TAU0      = 2.70           # baseline total goals/match for an even game (WC avg ~2.6-2.8)
TAU_SLOPE = 0.0012         # extra total goals per 1 Elo of mismatch (blowouts score more)
HOST_BONUS= 65.0           # Elo points added to a host nation (USA/MEX/CAN) in its matches
FORM_SD   = 70.0           # SD (Elo) of a team's per-tournament "form" random effect.
                           # Models rating uncertainty + squad form/injuries/draw-day luck;
                           # integrating over it regresses over-confident point forecasts.
ET_FRAC   = 30.0/90.0      # extra-time is 30 of 90 min: scale goal rate accordingly
PEN_SLOPE = 0.0004         # penalty-shootout edge per Elo point (tiny; shootouts ~ coin flip)
PEN_CAP   = 0.12           # max shootout edge (so P in [0.38, 0.62])

rng = np.random.default_rng(SEED)

# --------------------------------------------------------------------------- #
# 1.  LOAD GROUNDED INPUT DATA
# --------------------------------------------------------------------------- #
teams = pd.read_csv(os.path.join(DATA, "teams_2026.csv"))
teams = teams.reset_index(drop=True)
N_T   = len(teams)
assert N_T == 48, "expected 48 teams"

ELO_BASE = teams["elo"].to_numpy(float)
IS_HOST  = teams["host"].to_numpy(int)
# effective Elo: hosts play (essentially) at home all tournament; everyone else neutral.
ELO_ADJ  = ELO_BASE + HOST_BONUS * IS_HOST
GROUP    = teams["group"].to_numpy()
NAME     = teams["team"].to_numpy()
CONF     = teams["confederation"].to_numpy()

GROUP_LETTERS = list("ABCDEFGHIJKL")
# global indices per group, ordered by the 'slot' column (1..4)
g_idx = {}
for L in GROUP_LETTERS:
    sub = teams.index[teams["group"] == L].tolist()
    sub = sorted(sub, key=lambda i: teams.loc[i, "slot"])
    g_idx[L] = sub
    assert len(sub) == 4

with open(os.path.join(DATA, "bracket_structure.json")) as f:
    BRACKET = json.load(f)

# --------------------------------------------------------------------------- #
# 2.  MATCH MODEL  — Elo -> goals -> W/D/L  (the development chain)
# --------------------------------------------------------------------------- #
# 2a. Elo logistic expected score (probability of "winning" counting draw as 1/2):
#        E_A = 1 / (1 + 10^(-(R_A - R_B)/400))
def elo_expected(d):
    return 1.0 / (1.0 + 10.0 ** (-d / ELO_DIV))

# 2b. Goal model.  Team A ~ Poisson(lamA), B ~ Poisson(lamB), independent.
#     Parametrise by total goals tau = lamA+lamB and supremacy sigma = lamA-lamB.
#     We FIX tau(d)=TAU0+TAU_SLOPE*|d| and SOLVE sigma(d) so that the goal model's
#     implied expected score (via the Skellam distribution of A-B) EXACTLY matches
#     the Elo logistic expected score.  => the Poisson model is an internally
#     consistent re-parametrisation of Elo that also yields realistic scorelines.
def skellam_score(lamA, lamB):
    """Expected score for A = P(A>B) + 1/2 P(A=B) under independent Poisson."""
    p_draw = skellam.pmf(0, lamA, lamB)
    p_Awin = 1.0 - skellam.cdf(0, lamA, lamB)     # P(A-B >= 1)
    return p_Awin + 0.5 * p_draw

def solve_sigma(d):
    """Solve supremacy sigma>=0 for |d|; signed by d."""
    if d == 0:
        return 0.0
    dd  = abs(d)
    E   = elo_expected(dd)
    tau = TAU0 + TAU_SLOPE * dd
    hi  = tau - 0.10                               # keep lamB >= 0.05
    f   = lambda s: skellam_score((tau + s) / 2.0, (tau - s) / 2.0) - E
    if f(hi) <= 0:                                 # E beyond reachable max -> cap
        s = hi
    else:
        s = brentq(f, 1e-6, hi, xtol=1e-5)
    return s if d > 0 else -s

# Pre-compute sigma on a grid for fast vectorised interpolation.
DS  = np.arange(-900, 901, 2.0)
SIG = np.array([solve_sigma(d) for d in DS])

def lam_from_elo(eloA, eloB):
    """Vectorised: effective-Elo of A,B -> (lamA, lamB)."""
    d     = np.asarray(eloA, float) - np.asarray(eloB, float)
    sigma = np.interp(d, DS, SIG)
    tau   = TAU0 + TAU_SLOPE * np.abs(d)
    lamA  = np.clip((tau + sigma) / 2.0, 0.03, None)
    lamB  = np.clip((tau - sigma) / 2.0, 0.03, None)
    return lamA, lamB

def wdl(lamA, lamB):
    """(P(A win), P(draw), P(B win)) under independent Poisson via Skellam."""
    pd_ = skellam.pmf(0, lamA, lamB)
    pA  = 1.0 - skellam.cdf(0, lamA, lamB)
    pB  = skellam.cdf(-1, lamA, lamB)
    return pA, pd_, pB

# 2c. Calibration diagnostics: how well does the goal model reproduce Elo?
def calibration_report():
    ds = np.arange(0, 760, 20)
    rows = []
    for d in ds:
        lamA, lamB = lam_from_elo(d, 0.0)
        E_model = skellam_score(lamA, lamB)
        rows.append((d, elo_expected(d), float(E_model), float(lamA), float(lamB)))
    df = pd.DataFrame(rows, columns=["elo_diff","E_elo","E_model","lamA","lamB"])
    df["abs_err"] = (df["E_elo"] - df["E_model"]).abs()
    return df

# --------------------------------------------------------------------------- #
# 3.  POISSON-BINOMIAL  (group-stage analytic centrepiece)
# --------------------------------------------------------------------------- #
# A team plays 3 group games with win probabilities p1,p2,p3 (generally unequal).
# Its number of wins W = sum of 3 independent Bernoulli(pk)  ->  POISSON-BINOMIAL.
def poisson_binomial_pmf_conv(ps):
    """Exact PB pmf by direct convolution of Bernoullis. Returns P(W=0..n)."""
    dist = np.array([1.0])
    for p in ps:
        dist = np.convolve(dist, [1.0 - p, p])
    return dist

def poisson_binomial_pmf_dft(ps):
    """Exact PB pmf via the Discrete Fourier Transform of the characteristic
    function (independent method, used to PROVE the convolution result)."""
    n = len(ps)
    C = np.exp(2j * np.pi / (n + 1))
    pmf = np.zeros(n + 1, dtype=complex)
    for k in range(n + 1):
        prod = np.prod([1.0 + (C ** k - 1.0) * p for p in ps])
        pmf += (C ** (-np.arange(n + 1) * k)) * prod
    return np.real(pmf) / (n + 1)

PAIRS3 = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]   # the 6 matches of a 4-team group

def group_exact_analysis(group_letter):
    """Exact group-stage analysis for one group:
       - per team: 3 match (W,D,L) probabilities
       - per team: Poisson-binomial win-count distribution P(W=0,1,2,3)
       - per team: expected points  E[pts]=sum(3*pW + 1*pD)
       - per team: EXACT points-total distribution via 3^6=729 enumeration."""
    idx = g_idx[group_letter]
    e   = ELO_ADJ[idx]
    # match-level probabilities, indexed by the 6 pairs (lower local index = 'A')
    mp = {}
    for (a, b) in PAIRS3:
        lamA, lamB = lam_from_elo(e[a], e[b])
        pA, pdr, pB = wdl(lamA, lamB)
        mp[(a,b)] = (float(pA), float(pdr), float(pB), float(lamA), float(lamB))
    # per team win/draw/loss prob in each of its 3 matches
    team_match = {t: [] for t in range(4)}
    for (a,b) in PAIRS3:
        pA,pdr,pB,_,_ = mp[(a,b)]
        team_match[a].append((pA, pdr, pB))     # a's perspective
        team_match[b].append((pB, pdr, pA))     # b's perspective
    # Poisson-binomial win-count + expected points
    pb = {}
    epts = {}
    for t in range(4):
        winps = [m[0] for m in team_match[t]]
        drps  = [m[1] for m in team_match[t]]
        pb[t]   = poisson_binomial_pmf_conv(winps)
        epts[t] = sum(3*w + 1*dd for w, dd in zip(winps, drps))
    # EXACT joint points distribution via enumeration of 3^6 outcomes
    pts_dist = {t: defaultdict(float) for t in range(4)}
    # also exact P(each team is strict/tied group winner by points) handled in MC
    for combo in itertools.product([0,1,2], repeat=6):   # 0=A win,1=draw,2=B win
        prob = 1.0
        pts  = [0,0,0,0]
        for (mi,(a,b)) in enumerate(PAIRS3):
            pA,pdr,pB,_,_ = mp[(a,b)]
            o = combo[mi]
            if   o == 0: prob *= pA; pts[a]+=3
            elif o == 1: prob *= pdr; pts[a]+=1; pts[b]+=1
            else:        prob *= pB; pts[b]+=3
        for t in range(4):
            pts_dist[t][pts[t]] += prob
    return idx, mp, team_match, pb, epts, pts_dist

# --------------------------------------------------------------------------- #
# 4.  BEST-THIRD-PLACE COMBINATION TABLE  (FIFA 8-of-12 assignment)
# --------------------------------------------------------------------------- #
# The 8 R32 slots that receive a 3rd-place team, with their ELIGIBLE source
# groups (FIFA fixed schedule).  For any set of 8 qualifying groups we solve the
# bipartite assignment respecting eligibility (a system of distinct
# representatives) -- the official 495-row combination table is exactly such a
# pre-computed assignment.
THIRD_SLOTS = {            # slot match-id : eligible groups
    "M74": set("ABCDF"),
    "M77": set("CDFGH"),
    "M79": set("CEFHI"),
    "M80": set("EHIJK"),
    "M81": set("BEFIJ"),
    "M82": set("AEHIJ"),
    "M85": set("EFGIJ"),
    "M87": set("DEIJL"),
}
THIRD_SLOT_IDS = list(THIRD_SLOTS.keys())
GL_INDEX = {L:i for i,L in enumerate(GROUP_LETTERS)}

def build_third_place_table():
    """For every C(12,8)=495 subset of qualifying groups, pre-solve slot->group.
       Returns: dict mask(12-bit int) -> np.array of 8 group-indices (slot order)."""
    BIG = 1000
    elig = np.full((8, 12), BIG, float)
    for si, sid in enumerate(THIRD_SLOT_IDS):
        for L in THIRD_SLOTS[sid]:
            elig[si, GL_INDEX[L]] = 0.0
    table = {}
    n_violations = 0
    for combo in itertools.combinations(range(12), 8):     # qualifying groups
        cols = list(combo)
        cost = elig[:, cols]                               # 8 slots x 8 groups
        r, c = linear_sum_assignment(cost)                 # minimise ineligibility
        assign = np.empty(8, int)
        viol = 0
        for ri, ci in zip(r, c):
            assign[ri] = cols[ci]
            if cost[ri, ci] >= BIG:
                viol += 1
        if viol:
            n_violations += 1
        mask = 0
        for g in combo:
            mask |= (1 << g)
        table[mask] = assign
    return table, n_violations

# --------------------------------------------------------------------------- #
# 5.  MONTE-CARLO TOURNAMENT  (fully vectorised over N_SIMS)
# --------------------------------------------------------------------------- #
def simulate(n=N_SIMS, form_sd=FORM_SD):
    # Per-tournament team-strength random effect (one offset per team per replication).
    # form_sd=0 reproduces the exact point-estimate model (used to validate the engine).
    if form_sd > 0:
        ELO_SIM = ELO_ADJ[None, :] + rng.normal(0.0, form_sd, (n, N_T))
    else:
        ELO_SIM = np.broadcast_to(ELO_ADJ[None, :], (n, N_T))
    rowN = np.arange(n)

    # ---- 5a. GROUP STAGE -------------------------------------------------- #
    # per-group standings
    winner_g   = {}   # group -> (n,) global idx of group winner
    runner_g   = {}
    third_g    = {}   # group -> (n,) global idx of 3rd
    third_key  = {}   # group -> (n,3) [pts,gd,gf] of the 3rd team (for cross ranking)
    reach_r32  = np.zeros(N_T)        # P(qualify from group) numerator
    win_grp    = np.zeros(N_T)
    second_grp = np.zeros(N_T)
    third_cnt  = np.zeros(N_T)        # finished 3rd (qualified or not)
    advance_cnt= np.zeros(N_T)        # top-2
    epts_mc    = np.zeros(N_T)        # MC mean points (validation vs analytic)

    for L in GROUP_LETTERS:
        idx = np.array(g_idx[L])
        esim = ELO_SIM[:, idx]                       # (n,4) per-sim effective Elo
        pts = np.zeros((n, 4)); gd = np.zeros((n, 4)); gf = np.zeros((n, 4))
        for (a, b) in PAIRS3:
            lamA, lamB = lam_from_elo(esim[:, a], esim[:, b])
            ga = rng.poisson(lamA); gb = rng.poisson(lamB)
            gf[:, a] += ga; gf[:, b] += gb
            gd[:, a] += ga - gb; gd[:, b] += gb - ga
            pts[:, a] += np.where(ga > gb, 3, np.where(ga == gb, 1, 0))
            pts[:, b] += np.where(gb > ga, 3, np.where(gb == ga, 1, 0))
        rand = rng.random((n, 4))
        # rank: primary pts desc, then gd, gf, random  (lexsort: last key = primary)
        order = np.lexsort((rand, gf, gd, pts), axis=1)      # ascending -> worst first
        w  = idx[order[:, 3]]; r2 = idx[order[:, 2]]
        t3 = idx[order[:, 1]]; t4 = idx[order[:, 0]]
        winner_g[L] = w; runner_g[L] = r2; third_g[L] = t3
        # third team's tiebreak key
        row = np.arange(n)
        local3 = order[:, 1]
        third_key[L] = np.stack([pts[row, local3], gd[row, local3], gf[row, local3]], 1)
        np.add.at(win_grp,     w,  1); np.add.at(second_grp, r2, 1)
        np.add.at(third_cnt,   t3, 1); np.add.at(advance_cnt, w, 1); np.add.at(advance_cnt, r2, 1)
        for lc in range(4):
            np.add.at(epts_mc, idx[order[:, lc]], pts[row, order[:, lc]])

    # ---- 5b. RANK THE 12 THIRD-PLACE TEAMS, KEEP BEST 8 ------------------- #
    keys = np.stack([third_key[L] for L in GROUP_LETTERS], axis=1)   # (n,12,3)
    g3   = np.stack([third_g[L]   for L in GROUP_LETTERS], axis=1)   # (n,12) global idx
    rand12 = rng.random((n, 12))
    # rank groups' 3rd teams: pts,gd,gf desc
    okey = np.lexsort((rand12, keys[:,:,2], keys[:,:,1], keys[:,:,0]), axis=1)  # asc
    best8_local = okey[:, 4:]                       # columns -> best 8 group positions
    qualifies = np.zeros((n, 12), bool)
    np.put_along_axis(qualifies, best8_local, True, axis=1)
    # third-place global idx that qualified, by group
    for j, L in enumerate(GROUP_LETTERS):
        q = qualifies[:, j]
        np.add.at(reach_r32, g3[q, j], 1)
    # top-2 always reach R32
    for L in GROUP_LETTERS:
        np.add.at(reach_r32, winner_g[L], 1); np.add.at(reach_r32, runner_g[L], 1)

    # ---- 5c. ASSIGN QUALIFYING 3RD-PLACE TEAMS TO THE 8 SLOTS ------------- #
    table, n_viol = build_third_place_table()
    mask = (qualifies.astype(np.int64) << np.arange(12)).sum(1)     # (n,) 12-bit pattern
    # build per-mask assignment array (8 group indices in THIRD_SLOT order)
    uniq = np.unique(mask)
    assign_lut = np.zeros((mask.max() + 1, 8), int)
    for m in uniq:
        assign_lut[m] = table[int(m)]
    slot_group = assign_lut[mask]                                   # (n,8) group idx per slot
    row = np.arange(n)
    third_for_slot = {}
    for si, sid in enumerate(THIRD_SLOT_IDS):
        gsel = slot_group[:, si]                                    # (n,) group index
        third_for_slot[sid] = g3[row, gsel]                         # (n,) global team idx

    # ---- 5d. BUILD ROUND OF 32 PARTICIPANTS ------------------------------ #
    def resolve_token(tok):
        kind, val = tok.split(":")
        if kind == "W":  return winner_g[val]
        if kind == "R":  return runner_g[val]
        if kind == "3P": return None        # placeholder; filled from slot
    r32_part = {}
    for mid, (t1, t2) in BRACKET["r32"].items():
        p1 = third_for_slot[mid] if t1.startswith("3P") else resolve_token(t1)
        p2 = third_for_slot[mid] if t2.startswith("3P") else resolve_token(t2)
        r32_part[mid] = (p1, p2)

    # ---- 5e. KNOCKOUT MATCH SIMULATION ----------------------------------- #
    def play(idxA, idxB):
        eA = ELO_SIM[rowN, idxA]; eB = ELO_SIM[rowN, idxB]
        lamA, lamB = lam_from_elo(eA, eB)
        ga = rng.poisson(lamA); gb = rng.poisson(lamB)
        Awin = ga > gb; Bwin = gb > ga; draw = ~(Awin | Bwin)
        # extra time
        eta = rng.poisson(lamA * ET_FRAC); etb = rng.poisson(lamB * ET_FRAC)
        Aet = draw & (eta > etb); Bet = draw & (etb > eta); still = draw & (eta == etb)
        # penalties
        d = eA - eB
        pkA = 0.5 + np.clip(d * PEN_SLOPE, -PEN_CAP, PEN_CAP)
        coin = rng.random(len(idxA)) < pkA
        A_adv = Awin | Aet | (still & coin)
        return np.where(A_adv, idxA, idxB)

    reach = {r: np.zeros(N_T) for r in ["R16","QF","SF","FINAL","CHAMP"]}
    # R32 -> winners
    win32 = {}
    for mid, (p1, p2) in r32_part.items():
        wn = play(p1, p2); win32[mid] = wn
        np.add.at(reach["R16"], wn, 1)
    # R16
    win16 = {}
    for rid, (m1, m2) in BRACKET["r16"].items():
        wn = play(win32[m1], win32[m2]); win16[rid] = wn
        np.add.at(reach["QF"], wn, 1)
    # QF
    winqf = {}
    for qid, (r1, r2) in BRACKET["qf"].items():
        wn = play(win16[r1], win16[r2]); winqf[qid] = wn
        np.add.at(reach["SF"], wn, 1)
    # SF
    winsf = {}
    for sid_, (q1, q2) in BRACKET["sf"].items():
        wn = play(winqf[q1], winqf[q2]); winsf[sid_] = wn
        np.add.at(reach["FINAL"], wn, 1)
    # FINAL
    fkey = list(BRACKET["final"].keys())[0]
    s1, s2 = BRACKET["final"][fkey]
    champ = play(winsf[s1], winsf[s2])
    np.add.at(reach["CHAMP"], champ, 1)

    res = pd.DataFrame({
        "team": NAME, "group": GROUP, "confederation": CONF,
        "elo": ELO_BASE, "host": IS_HOST,
        "E_pts_mc": epts_mc / n,
        "P_win_group": win_grp / n, "P_runner_up": second_grp / n,
        "P_third": third_cnt / n, "P_top2": advance_cnt / n,
        "P_reach_R32": reach_r32 / n,
        "P_reach_R16": reach["R16"] / n, "P_reach_QF": reach["QF"] / n,
        "P_reach_SF": reach["SF"] / n, "P_reach_Final": reach["FINAL"] / n,
        "P_champion": reach["CHAMP"] / n,
    })
    return res, n_viol

# --------------------------------------------------------------------------- #
# 6.  MARKET DE-VIG + CONSENSUS BLEND
# --------------------------------------------------------------------------- #
def market_probabilities():
    odds = teams["market_dec_odds"].to_numpy(float)
    raw  = np.where(np.isfinite(odds), 1.0 / odds, np.nan)
    listed = np.isfinite(raw)
    # Allocate a small residual to the 30 unlisted teams (long shots): 4% total.
    UNLISTED_TOTAL = 0.04
    n_unlisted = (~listed).sum()
    implied = raw.copy()
    s_listed = np.nansum(raw)                      # overround-inflated sum of listed
    # de-vig listed to (1 - UNLISTED_TOTAL); spread residual over unlisted by Elo softmax
    implied_listed = raw[listed] / s_listed * (1.0 - UNLISTED_TOTAL)
    out = np.zeros(N_T)
    out[listed] = implied_listed
    if n_unlisted:
        e = ELO_BASE[~listed]
        w = np.exp((e - e.max()) / 90.0)           # soft weight by Elo
        out[~listed] = UNLISTED_TOTAL * w / w.sum()
    return out

# --------------------------------------------------------------------------- #
# 7.  RUN EVERYTHING + WRITE OUTPUTS
# --------------------------------------------------------------------------- #
def main():
    print("="*70)
    print(" 2026 FIFA WORLD CUP FORECAST ENGINE")
    print("="*70)
    print(f" seed={SEED}  N_SIMS={N_SIMS:,}  host_bonus={HOST_BONUS} Elo")

    # --- calibration ---
    cal = calibration_report()
    print("\n[1] Elo->goal model calibration (max |E_elo - E_model|):",
          round(cal['abs_err'].max(), 4))
    cal.to_csv(os.path.join(OUT, "calibration.csv"), index=False)

    # --- exact group analysis + Technical Appendix A ---
    print("[2] Exact group-stage Poisson-binomial analysis ...")
    appendixA = []
    group_meta = {}
    for L in GROUP_LETTERS:
        idx, mp, tm, pb, epts, pts_dist = group_exact_analysis(L)
        group_meta[L] = (idx, mp, tm, pb, epts, pts_dist)
        for li, gt in enumerate(idx):
            winps = [m[0] for m in tm[li]]
            drps  = [m[1] for m in tm[li]]
            lsps  = [m[2] for m in tm[li]]
            pbd   = pb[li]
            pd_full = pts_dist[li]
            row = {
                "group": L, "team": NAME[gt], "elo": ELO_BASE[gt],
                "p_win_m1": round(winps[0],4),"p_win_m2": round(winps[1],4),"p_win_m3": round(winps[2],4),
                "p_draw_avg": round(np.mean(drps),4), "p_loss_avg": round(np.mean(lsps),4),
                "E_points_analytic": round(epts[li],4),
                "PB_P_0win": round(pbd[0],4),"PB_P_1win": round(pbd[1],4),
                "PB_P_2win": round(pbd[2],4),"PB_P_3win": round(pbd[3],4),
            }
            for k in range(0,10):
                row[f"P_pts_{k}"] = round(pd_full.get(k,0.0),4)
            appendixA.append(row)
    dfA = pd.DataFrame(appendixA)
    dfA.to_csv(os.path.join(OUT, "technical_appendix_A_poisson_binomial.csv"), index=False)

    # validate PB convolution vs DFT on one team
    sampleps = [m[0] for m in group_meta["I"][2][0]]   # France's win probs
    conv = poisson_binomial_pmf_conv(sampleps)
    dft  = poisson_binomial_pmf_dft(sampleps)
    print("    PB convolution vs DFT max diff:", round(float(np.max(np.abs(conv-dft))),12))

    # --- ENGINE VALIDATION: form_sd=0 MC must reproduce the exact analytic math ---
    print("[3] Engine validation run (form_sd=0, n=100k) vs exact analytic ...")
    val, _ = simulate(100_000, form_sd=0.0)
    ana = dfA.set_index("team")["E_points_analytic"]
    valv = val.set_index("team")
    err = (valv["E_pts_mc"] - ana).abs()
    print("    max |E[pts]_MC(form=0) - E[pts]_analytic|:", round(err.max(), 4))

    # --- PRODUCTION Monte Carlo (with form uncertainty) ---
    print(f"[4] Production Monte-Carlo: {N_SIMS:,} sims, form_sd={FORM_SD} Elo ...")
    res, n_viol = simulate(N_SIMS, FORM_SD)
    print(f"    3rd-place assignment eligibility violations among 495 patterns: {n_viol}")
    res = res.set_index("team"); res["E_pts_analytic"] = ana; res = res.reset_index()

    # --- SENSITIVITY to the form_sd assumption ---
    sens_rows = []
    for sd in [0, 40, 70, 100]:
        rs, _ = simulate(60_000, form_sd=sd)
        rs = rs.set_index("team")
        sens_rows.append({"form_sd": sd, **{t: round(rs.loc[t,"P_champion"]*100,2)
                          for t in ["Spain","Argentina","France","England","Portugal","Brazil"]}})
    pd.DataFrame(sens_rows).to_csv(os.path.join(OUT,"sensitivity_form_sd.csv"), index=False)

    # --- market + consensus ---
    res["P_market"] = market_probabilities()
    # consensus: geometric blend in log-odds space, 55% model / 45% market
    def logit(p): return np.log(np.clip(p,1e-9,1-1e-9)/(1-np.clip(p,1e-9,1-1e-9)))
    wmodel = 0.55
    blend = wmodel*logit(res["P_champion"]) + (1-wmodel)*logit(res["P_market"])
    cons = 1/(1+np.exp(-blend))
    res["P_consensus"] = cons / cons.sum()
    res["value_vs_market"] = res["P_champion"] - res["P_market"]
    # Monte-Carlo standard error on champion prob
    res["champ_SE"] = np.sqrt(res["P_champion"]*(1-res["P_champion"])/N_SIMS)

    res = res.sort_values("P_consensus", ascending=False).reset_index(drop=True)
    res.insert(0, "rank", res.index+1)

    # round columns ordering
    res.to_csv(os.path.join(OUT, "forecast_full.csv"), index=False)

    # champion table
    champ = res[["rank","team","group","confederation","elo","P_champion","champ_SE",
                 "P_market","P_consensus","value_vs_market",
                 "P_reach_Final","P_reach_SF","P_reach_QF","P_reach_R16","P_reach_R32"]].copy()
    champ.to_csv(os.path.join(OUT, "champion_probabilities.csv"), index=False)

    # group stage table
    grp = res[["team","group","elo","E_pts_mc","P_win_group","P_runner_up",
               "P_third","P_top2","P_reach_R32"]].sort_values(
               ["group","P_win_group"], ascending=[True,False])
    grp.to_csv(os.path.join(OUT, "group_stage_probabilities.csv"), index=False)

    # match probability matrix (intra-group) ---------------------------------
    mm_rows = []
    for L in GROUP_LETTERS:
        idx, mp, *_ = group_meta[L]
        for (a,b) in PAIRS3:
            pA,pdr,pB,lamA,lamB = mp[(a,b)]
            mm_rows.append({"group":L,"teamA":NAME[idx[a]],"teamB":NAME[idx[b]],
                "P_A_win":round(pA,4),"P_draw":round(pdr,4),"P_B_win":round(pB,4),
                "xG_A":round(lamA,3),"xG_B":round(lamB,3)})
    pd.DataFrame(mm_rows).to_csv(os.path.join(OUT,"match_matrix_group.csv"), index=False)

    # full 48x48 expected-score matrix (neutral venue) -----------------------
    M = np.zeros((N_T,N_T))
    for i in range(N_T):
        lamA, lamB = lam_from_elo(np.full(N_T, ELO_BASE[i]), ELO_BASE)
        M[i] = skellam_score(lamA, lamB)
    np.fill_diagonal(M, 0.5)
    pd.DataFrame(M, index=NAME, columns=NAME).round(3).to_csv(
        os.path.join(OUT,"expected_score_matrix_48x48.csv"))

    print("\n[5] TOP 16 (consensus):")
    for _,r in res.head(16).iterrows():
        print(f"   {int(r['rank']):2d}. {r['team']:<16} champ={r['P_champion']*100:5.2f}%"
              f"  mkt={r['P_market']*100:5.2f}%  consensus={r['P_consensus']*100:5.2f}%")

    print("\n[6] writing CSV outputs to outputs/ ... done")
    return res, dfA, cal, group_meta

if __name__ == "__main__":
    res, dfA, cal, group_meta = main()
