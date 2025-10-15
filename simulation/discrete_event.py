from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Set

import simpy
import random
import networkx as nx


@dataclass
class DESimResult:
    total_infected: int
    time_elapsed: float


def run_discrete_event(
    g: nx.DiGraph,
    initial_infected: Iterable[int],
    verified_nodes: Optional[Set[int]] = None,
    max_time: float = 20.0,
    seed: int = 42,
) -> DESimResult:
    """
    Discrete-event propagation: infections are Poisson processes per susceptible edge.
    Each active node schedules infection attempts with exponentially distributed waiting times
    parameterized by the edge weight (lambda).
    Verified nodes are immune and do not spread.
    """
    env = simpy.Environment()
    rng = random.Random(seed)

    infected: Set[int] = set(n for n in initial_infected if verified_nodes is None or n not in verified_nodes)
    activated: Set[int] = set(infected)

    def try_infect(u: int, v: int):
        if verified_nodes is not None and (u in verified_nodes or v in verified_nodes):
            return
        if v in activated:
            return
        rate = float(g[u][v].get("weight", 0.1))
        if rate <= 0:
            return
        # Sample exponential waiting time
        wait = rng.expovariate(rate)
        yield env.timeout(wait)
        if v not in activated:
            activated.add(v)
            env.process(spread_from(v))

    def spread_from(u: int):
        for v in g.successors(u):
            yield env.process(try_infect(u, v))

    for u in list(infected):
        env.process(spread_from(u))

    env.run(until=max_time)
    return DESimResult(total_infected=len(activated), time_elapsed=max_time)
