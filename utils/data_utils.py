from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import csv
import random


Edge = Tuple[int, int, float]


@dataclass
class EdgeList:
    edges: List[Edge]

    @staticmethod
    def read_from_csv(path: Path) -> "EdgeList":
        edges: List[Edge] = []
        with path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                source = int(row["source"]) if row["source"] != "" else None
                target = int(row["target"]) if row["target"] != "" else None
                weight = float(row["weight"]) if row["weight"] != "" else 1.0
                if source is None or target is None:
                    continue
                edges.append((source, target, weight))
        return EdgeList(edges)

    @staticmethod
    def synthetic_er(num_nodes: int, edge_prob: float, weight_low: float = 0.1, weight_high: float = 0.9, seed: int = 42) -> "EdgeList":
        rnd = random.Random(seed)
        edges: List[Edge] = []
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i == j:
                    continue
                if rnd.random() < edge_prob:
                    w = rnd.uniform(weight_low, weight_high)
                    edges.append((i, j, w))
        return EdgeList(edges)

    def to_csv(self, path: Path) -> None:
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target", "weight"])
            writer.writerows(self.edges)

    def nodes(self) -> List[int]:
        node_set = set()
        for u, v, _ in self.edges:
            node_set.add(u)
            node_set.add(v)
        return sorted(node_set)

    def __iter__(self) -> Iterable[Edge]:
        return iter(self.edges)
