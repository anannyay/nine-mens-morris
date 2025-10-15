from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence, Set

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


@dataclass
class PlotPaths:
    before_png: Path
    after_png: Path
    influence_png: Path


def draw_graph(g: nx.DiGraph, path: Path, verified: Optional[Set[int]] = None, title: str = "Graph") -> None:
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(g, seed=42)
    node_color = []
    for n in g.nodes:
        if verified is not None and n in verified:
            node_color.append("tab:green")
        else:
            node_color.append("tab:blue")
    nx.draw_networkx_nodes(g, pos, node_color=node_color, node_size=120, alpha=0.9)
    nx.draw_networkx_edges(g, pos, alpha=0.4, arrows=True, arrowsize=10)
    nx.draw_networkx_labels(g, pos, font_size=8)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def plot_influence(g: nx.DiGraph, scores: Dict[int, float], path: Path) -> None:
    nodes = list(scores.keys())
    values = [scores[n] for n in nodes]
    order = np.argsort(values)[::-1]
    nodes_sorted = [nodes[i] for i in order]
    values_sorted = [values[i] for i in order]

    plt.figure(figsize=(10, 4))
    plt.bar(range(len(nodes_sorted)), values_sorted)
    plt.xticks(range(len(nodes_sorted)), nodes_sorted, rotation=90)
    plt.ylabel("influence score")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def plot_sim_convergence_series(series: Dict[str, Sequence[int]], path: Path, window: int = 10) -> None:
    """
    Plot per-run infections for multiple series (e.g., before/after) with optional moving average.
    """
    plt.figure(figsize=(10, 4))
    for label, values in series.items():
        if len(values) == 0:
            continue
        x = list(range(1, len(values) + 1))
        plt.plot(x, values, alpha=0.3, linewidth=1.0, label=f"{label} (per-run)")
        if window > 1 and len(values) >= window:
            import numpy as np

            mv = np.convolve(values, np.ones(window) / window, mode="valid")
            x_avg = list(range(window, len(values) + 1))
            plt.plot(x_avg, mv, linewidth=2.0, label=f"{label} (moving avg)")
    plt.xlabel("run")
    plt.ylabel("infected count")
    plt.title("Monte Carlo convergence")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
