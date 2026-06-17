import pandas as pd
import numpy as np
import math

# Expanded 48-team roster with estimated Elo ratings for 2026
teams = [
    # Group A
    ("Mexico", "A", 1880), ("Cameroon", "A", 1650), ("Sweden", "A", 1790), ("New Zealand", "A", 1550),
    # Group B
    ("USA", "B", 1850), ("Mali", "B", 1680), ("Serbia", "B", 1820), ("Saudi Arabia", "B", 1580),
    # Group C
    ("Canada", "C", 1750), ("Poland", "C", 1760), ("Ecuador", "C", 1810), ("South Africa", "C", 1590),
    # Group D
    ("France", "D", 2135), ("Algeria", "D", 1720), ("Costa Rica", "D", 1610), ("Uzbekistan", "D", 1520),
    # Group E
    ("Brazil", "E", 2065), ("Hungary", "E", 1780), ("Ivory Coast", "E", 1700), ("Panama", "E", 1630),
    # Group F
    ("England", "F", 2070), ("Morocco", "F", 1840), ("Paraguay", "F", 1690), ("Jamaica", "F", 1570),
    # Group G
    ("Spain", "G", 2105), ("Senegal", "G", 1800), ("Australia", "G", 1740), ("Venezuela", "G", 1680),
    # Group H
    ("Argentina", "H", 2140), ("Switzerland", "H", 1860), ("Nigeria", "H", 1710), ("Qatar", "H", 1540),
    # Group I
    ("Germany", "I", 2050), ("Japan", "I", 1830), ("Peru", "I", 1730), ("Egypt", "I", 1670),
    # Group J
    ("Portugal", "J", 2010), ("Colombia", "J", 1920), ("Wales", "J", 1750), ("Iran", "J", 1700),
    # Group K
    ("Netherlands", "K", 1990), ("Uruguay", "K", 1960), ("Tunisia", "K", 1660), ("South Korea", "K", 1770),
    # Group L
    ("Italy", "L", 1980), ("Croatia", "L", 1940), ("Chile", "L", 1720), ("Ghana", "L", 1640)
]

def expected_goals_from_elo(elo1, elo2):
    # Simplified Elo to xG conversion factor
    elo_diff = elo1 - elo2
    xg1 = max(0.5, 1.2 + (elo_diff / 400.0) * 1.5)
    xg2 = max(0.5, 1.2 - (elo_diff / 400.0) * 1.5)
    return xg1, xg2

def poisson_match_prob(xg1, xg2, max_goals=5):
    prob_1_win = 0
    prob_draw = 0
    prob_2_win = 0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            pi = (math.exp(-xg1) * (xg1**i)) / math.factorial(i)
            pj = (math.exp(-xg2) * (xg2**j)) / math.factorial(j)
            p = pi * pj
            if i > j: prob_1_win += p
            elif i == j: prob_draw += p
            else: prob_2_win += p
    return prob_1_win, prob_draw, prob_2_win

results = []

groups = {}
for team, group, elo in teams:
    if group not in groups:
        groups[group] = []
    groups[group].append({"name": team, "elo": elo})

for group_name, members in groups.items():
    exp_pts = {m["name"]: 0 for m in members}

    # Round robin
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            t1 = members[i]
            t2 = members[j]
            xg1, xg2 = expected_goals_from_elo(t1["elo"], t2["elo"])
            p1_win, p_draw, p2_win = poisson_match_prob(xg1, xg2)

            exp_pts[t1["name"]] += (p1_win * 3) + (p_draw * 1)
            exp_pts[t2["name"]] += (p2_win * 3) + (p_draw * 1)

    for m in members:
        results.append({
            "Team": m["name"],
            "Group": group_name,
            "Elo": m["elo"],
            "Expected_Points": round(exp_pts[m["name"]], 2)
        })

df = pd.DataFrame(results)

# Calculate placement probability (simplified approximation based on expected points)
df['Prob_1st'] = df.groupby('Group')['Expected_Points'].transform(lambda x: x / x.sum())
df['Prob_Advance_Top2'] = df.groupby('Group')['Expected_Points'].transform(lambda x: np.minimum(1.0, (x / x.sum()) * 2))

df = df.sort_values(by=['Group', 'Expected_Points'], ascending=[True, False]).reset_index(drop=True)

df.to_csv("48_team_group_stage_poisson.csv", index=False)
print("Generated Technical Appendix A: 48_team_group_stage_poisson.csv")
