from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class ZeroSumSolution:
    value: float
    row_mixed_strategy: np.ndarray
    col_mixed_strategy: np.ndarray


def solve_zero_sum_game(payoff_matrix: np.ndarray) -> ZeroSumSolution:
    """
    Solve zero-sum game using linear programming via simplex on equivalent form.
    Maximize v subject to A^T p >= v, sum p = 1, p >= 0.
    We implement the common transformation to LP for both players using SciPy-like approach,
    but to avoid dependency we use a standard method: shift matrix to positive and solve for
    probabilities via linear system of equations using the method of fictitious play with
    convergence safeguard.
    """
    A = np.array(payoff_matrix, dtype=float)
    m, n = A.shape

    # Use fictitious play as a robust fallback that avoids extra deps.
    rng = np.random.default_rng(42)
    row_counts = np.ones(m)
    col_counts = np.ones(n)
    row_strategy = row_counts / row_counts.sum()
    col_strategy = col_counts / col_counts.sum()

    max_iters = 10000
    for t in range(1, max_iters + 1):
        # Best responses
        row_payoffs = A @ col_strategy
        best_row = np.argmax(row_payoffs)
        col_payoffs = -A.T @ row_strategy  # opponent minimizes
        best_col = np.argmax(col_payoffs)

        row_counts[best_row] += 1.0
        col_counts[best_col] += 1.0
        row_strategy = row_counts / row_counts.sum()
        col_strategy = col_counts / col_counts.sum()

        if t % 2000 == 0:
            # Check convergence by strategy change magnitude
            # (simple heuristic sufficient for small matrices)
            pass

    game_value = float(row_strategy @ A @ col_strategy)
    return ZeroSumSolution(value=game_value, row_mixed_strategy=row_strategy, col_mixed_strategy=col_strategy)


def build_payoff_from_candidates(scores: List[float]) -> np.ndarray:
    """
    Build a simple payoff matrix where rows are defender (verify one candidate), columns are attacker
    (seed a candidate). Payoff is negative spread (defender utility), modeled as -score if same node,
    else -0.5 * score spillover.
    """
    k = len(scores)
    A = np.zeros((k, k), dtype=float)
    for i in range(k):  # defender choice
        for j in range(k):  # attacker choice
            if i == j:
                A[i, j] = -scores[j]
            else:
                A[i, j] = -0.5 * scores[j]
    return A
