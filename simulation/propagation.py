from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set

import math
import random

import networkx as nx


@dataclass
class SimulationStats:
    avg_infected: float
    std_infected: float
    runs: int
    infections_per_run: List[int]


def independent_cascade(
    g: nx.DiGraph,
    initial_infected: Iterable[int],
    transmission_prob_attr: str = "weight",
    verified_nodes: Optional[Set[int]] = None,
    rng: Optional[random.Random] = None,
) -> Set[int]:
    """
    Simple independent cascade: each activated node gets one chance to activate neighbors
    with probability equal to edge weight. Verified nodes are immune to activation and do
    not activate others.
    """
    if rng is None:
        rng = random.Random(42)

    infected: Set[int] = set(n for n in initial_infected if verified_nodes is None or n not in verified_nodes)
    frontier: List[int] = list(infected)
    activated: Set[int] = set(infected)

    while frontier:
        new_frontier: List[int] = []
        for u in frontier:
            if verified_nodes is not None and u in verified_nodes:
                continue
            for v in g.successors(u):
                if verified_nodes is not None and v in verified_nodes:
                    continue
                if v in activated:
                    continue
                p = float(g[u][v].get(transmission_prob_attr, 0.1))
                if rng.random() < p:
                    activated.add(v)
                    new_frontier.append(v)
        frontier = new_frontier

    return activated


def monte_carlo_spread(
    g: nx.DiGraph,
    seed_nodes: Iterable[int],
    verified_nodes: Optional[Set[int]] = None,
    runs: int = 100,
    seed: int = 42,
) -> SimulationStats:
    rng = random.Random(seed)
    counts: List[int] = []
    for _ in range(runs):
        infected = independent_cascade(g, seed_nodes, verified_nodes=verified_nodes, rng=rng)
        counts.append(len(infected))
    if len(counts) == 0:
        return SimulationStats(avg_infected=0.0, std_infected=0.0, runs=0, infections_per_run=[])
    avg = sum(counts) / len(counts)
    var = sum((c - avg) ** 2 for c in counts) / len(counts)
    std = math.sqrt(var)
    return SimulationStats(avg_infected=avg, std_infected=std, runs=len(counts), infections_per_run=counts)
