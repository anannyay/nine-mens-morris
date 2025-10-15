from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import networkx as nx

from utils.data_utils import EdgeList


@dataclass
class GeneratedGraph:
    graph: nx.DiGraph


def build_graph_from_edges(edge_list: EdgeList) -> GeneratedGraph:
    g = nx.DiGraph()
    for u, v, w in edge_list:
        g.add_edge(int(u), int(v), weight=float(w))
    return GeneratedGraph(graph=g)


def assign_node_attributes_by_incoming_weight(g: nx.DiGraph) -> None:
    influence = {}
    for node in g.nodes:
        total_influence = 0.0
        for pred in g.predecessors(node):
            total_influence += float(g[pred][node].get("weight", 1.0))
        influence[node] = total_influence
    nx.set_node_attributes(g, influence, name="influence")


def ensure_connected_components(g: nx.DiGraph) -> None:
    if g.number_of_nodes() == 0:
        return
    # No-op for now; directed graphs have weakly connected components.
    # This function is a placeholder to consolidate preprocessing if needed.
    return
