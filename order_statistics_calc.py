import math
import numpy as np

def poisson_cdf(lam, k):
    """Calculate the cumulative distribution function for Poisson(lam) at k."""
    cdf = 0.0
    for i in range(k + 1):
        cdf += (math.exp(-lam) * (lam**i)) / math.factorial(i)
    return cdf

def expected_maximum_order_statistic(n_teams, expected_goals_per_team, max_k=30):
    """
    Calculate the expected maximum goals scored by ANY team in the tournament.
    Uses the CDF of the maximum order statistic for i.i.d. variables:
    F_max(k) = [F_single(k)]^N
    E[Max] = sum_{k=0}^inf (1 - F_max(k))
    """
    expected_max = 0.0
    # Assuming teams play max 7 games (if reaching final/third-place match)
    # Average expected goals across the tournament for top teams ~ 12
    # Let's say we have N highly competitive teams pulling from similar distribution

    for k in range(max_k):
        cdf_single = poisson_cdf(expected_goals_per_team, k)
        cdf_max = cdf_single ** n_teams

        # P(Max > k) = 1 - P(Max <= k)
        prob_max_gt_k = 1.0 - cdf_max
        expected_max += prob_max_gt_k

    return expected_max

if __name__ == "__main__":
    print("Technical Appendix B: Order Statistics Calculation")
    print("--------------------------------------------------")

    # Let's assume there are 8 elite teams (Tier 1 & 2) that are likely to play 7 matches
    # Average xG per match for these elite teams ~ 1.8
    # Total Expected Goals over 7 matches ~ 12.6
    lam_elite = 12.6
    n_elite_teams = 8

    expected_max_goals = expected_maximum_order_statistic(n_elite_teams, lam_elite, max_k=40)

    print(f"Number of Elite Teams (n): {n_elite_teams}")
    print(f"Expected Goals per Elite Team over Tournament (λ): {lam_elite}")
    print(f"Expected Maximum Goals by the Highest Scoring Team: {expected_max_goals:.2f}")

    # Calculate probability that the top scorer team exceeds 15 goals
    cdf_15_single = poisson_cdf(lam_elite, 15)
    cdf_15_max = cdf_15_single ** n_elite_teams
    prob_exceeds_15 = 1.0 - cdf_15_max

    print(f"Probability that at least one team scores > 15 goals: {prob_exceeds_15 * 100:.2f}%")
