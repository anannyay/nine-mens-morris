from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    data_dir: Path
    results_dir: Path

    @staticmethod
    def from_root(root: Optional[Path] = None) -> "ProjectPaths":
        base = Path("/workspace") if root is None else root
        data = base / "data"
        results = base / "results"
        results.mkdir(parents=True, exist_ok=True)
        data.mkdir(parents=True, exist_ok=True)
        return ProjectPaths(root=base, data_dir=data, results_dir=results)


@dataclass
class ExperimentConfig:
    random_seed: int = 42
    verification_budget: int = 5
    num_monte_carlo_runs: int = 200
    attacker_seed_count: int = 3
    max_candidates_for_game: int = 8
    discrete_event_max_time: float = 20.0

    # Graph generation defaults (used if no CSV provided)
    synthetic_num_nodes: int = 50
    synthetic_edge_prob: float = 0.06


@dataclass
class IOConfig:
    edges_csv_filename: str = "synthetic_edges.csv"
    graph_gexf_filename: str = "network_export.gexf"
    before_png: str = "graph_before.png"
    after_png: str = "graph_after.png"
    influence_png: str = "node_influence.png"
    sim_convergence_png: str = "simulation_convergence.png"
    plotly_html: str = "graph_interactive.html"


@dataclass
class Config:
    paths: ProjectPaths
    experiment: ExperimentConfig
    io: IOConfig

    @staticmethod
    def default(root: Optional[Path] = None) -> "Config":
        return Config(
            paths=ProjectPaths.from_root(root),
            experiment=ExperimentConfig(),
            io=IOConfig(),
        )
