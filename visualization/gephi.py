from __future__ import annotations

from pathlib import Path
from typing import Optional

import networkx as nx


def export_gexf(g: nx.DiGraph, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(g, path)
