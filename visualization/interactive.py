from __future__ import annotations

from pathlib import Path
from typing import Optional, Set

import networkx as nx
import plotly.graph_objects as go


def plotly_interactive_graph(g: nx.DiGraph, path: Path, verified: Optional[Set[int]] = None, title: str = "Interactive Graph") -> None:
    pos = nx.spring_layout(g, seed=42)

    x_nodes = [pos[k][0] for k in g.nodes()]
    y_nodes = [pos[k][1] for k in g.nodes()]

    edge_x = []
    edge_y = []
    for u, v in g.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color="#888"), hoverinfo='none', mode='lines')

    node_color = []
    for n in g.nodes():
        if verified is not None and n in verified:
            node_color.append("green")
        else:
            node_color.append("blue")

    node_trace = go.Scatter(
        x=x_nodes,
        y=y_nodes,
        mode='markers+text',
        text=[str(n) for n in g.nodes()],
        textposition='top center',
        marker=dict(color=node_color, size=10, line_width=2)
    )

    fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(title=title, showlegend=False, hovermode='closest'))
    fig.write_html(str(path))
