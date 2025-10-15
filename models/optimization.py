from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Set, Tuple

import networkx as nx
import pulp


@dataclass
class OptimizationResult:
    objective_value: float
    verified_nodes: Set[int]
    node_scores: Dict[int, float]


def compute_node_influence_scores(g: nx.DiGraph) -> Dict[int, float]:
    """
    Influence score combines PageRank and weighted in-degree.
    """
    pagerank = nx.pagerank(g, weight="weight")
    weighted_in_degree: Dict[int, float] = {}
    for node in g.nodes:
        s = 0.0
        for pred in g.predecessors(node):
            s += float(g[pred][node].get("weight", 1.0))
        weighted_in_degree[node] = s

    # Normalize and combine
    def normalize(d: Dict[int, float]) -> Dict[int, float]:
        vals = list(d.values())
        if not vals:
            return d
        vmin, vmax = min(vals), max(vals)
        if vmax - vmin < 1e-12:
            return {k: 0.0 for k in d}
        return {k: (v - vmin) / (vmax - vmin) for k, v in d.items()}

    pr_n = normalize(pagerank)
    indeg_n = normalize(weighted_in_degree)
    scores = {n: 0.6 * pr_n.get(n, 0.0) + 0.4 * indeg_n.get(n, 0.0) for n in g.nodes}
    return scores


def solve_verification_selection(g: nx.DiGraph, budget: int) -> OptimizationResult:
    """
    0-1 IP: choose nodes to verify.
    Decision: x_i in {0,1} if node i is verified.
    Objective: minimize sum(score_i * (1 - x_i)) = const - sum(score_i * x_i)
    Equivalent to maximize sum(score_i * x_i) subject to sum(x_i) <= budget.
    """
    scores = compute_node_influence_scores(g)

    prob = pulp.LpProblem("verify_selection", pulp.LpMaximize)
    x_vars: Dict[int, pulp.LpVariable] = {n: pulp.LpVariable(f"x_{n}", lowBound=0, upBound=1, cat="Binary") for n in g.nodes}

    prob += pulp.lpSum(scores[n] * x_vars[n] for n in g.nodes), "maximize_score"
    prob += pulp.lpSum(x_vars[n] for n in g.nodes) <= int(budget), "budget_constraint"

    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)

    chosen: Set[int] = {n for n in g.nodes if pulp.value(x_vars[n]) is not None and pulp.value(x_vars[n]) > 0.5}
    obj = pulp.value(prob.objective) if prob.objective is not None else 0.0

    # Objective formulated as maximize protected score; convert to residual misinformation surrogate
    total_score = sum(scores.values())
    residual = float(total_score - (obj if obj is not None else 0.0))
    return OptimizationResult(objective_value=residual, verified_nodes=chosen, node_scores=scores)
