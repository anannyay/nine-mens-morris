from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import networkx as nx


@dataclass
class NodeMetrics:
    degree_centrality: Dict[int, float]
    betweenness_centrality: Dict[int, float]
    pagerank: Dict[int, float]

    def top_k(self, k: int = 10) -> Dict[str, List[Tuple[int, float]]]:
        def top(d: Dict[int, float]) -> List[Tuple[int, float]]:
            return sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:k]

        return {
            "degree": top(self.degree_centrality),
            "betweenness": top(self.betweenness_centrality),
            "pagerank": top(self.pagerank),
        }


def compute_node_metrics(g: nx.DiGraph) -> NodeMetrics:
    # For directed graphs, degree_centrality uses in+out degree normalized
    degree_centrality = nx.degree_centrality(g)
    betweenness_centrality = nx.betweenness_centrality(g, normalized=True)
    pagerank = nx.pagerank(g, weight="weight")
    return NodeMetrics(
        degree_centrality=degree_centrality,
        betweenness_centrality=betweenness_centrality,
        pagerank=pagerank,
    )
