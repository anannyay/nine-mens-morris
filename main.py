from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Set

import numpy as np
import networkx as nx

from utils.config import Config
from utils.data_utils import EdgeList
from utils.logging_utils import setup_logger
from network.generator import build_graph_from_edges, assign_node_attributes_by_incoming_weight
from network.analysis import compute_node_metrics
from models.optimization import solve_verification_selection, compute_node_influence_scores
from models.game_theory import build_payoff_from_candidates, solve_zero_sum_game
from models.allocation import hungarian, modi_method
from simulation.propagation import monte_carlo_spread
from simulation.discrete_event import run_discrete_event
from visualization.plots import draw_graph, plot_influence, plot_sim_convergence_series
from visualization.interactive import plotly_interactive_graph
from visualization.gephi import export_gexf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Social Media Misinformation Containment")
    parser.add_argument("--use-synthetic", action="store_true", help="Ignore CSV and generate ER graph")
    parser.add_argument("--budget", type=int, default=None, help="Verification budget override")
    parser.add_argument("--mc-runs", type=int, default=None, help="Monte Carlo runs override")
    parser.add_argument("--seed", type=int, default=None, help="Random seed override")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = Config.default()
    if args.budget is not None:
        cfg.experiment.verification_budget = int(args.budget)
    if args.mc_runs is not None:
        cfg.experiment.num_monte_carlo_runs = int(args.mc_runs)
    if args.seed is not None:
        cfg.experiment.random_seed = int(args.seed)

    log = setup_logger()
    log.info("Starting workflow")

    # Load or synthesize network
    edges_path = cfg.paths.data_dir / cfg.io.edges_csv_filename
    if args.use_synthetic or not edges_path.exists():
        log.info("Generating synthetic ER edge list")
        elist = EdgeList.synthetic_er(
            num_nodes=cfg.experiment.synthetic_num_nodes,
            edge_prob=cfg.experiment.synthetic_edge_prob,
            seed=cfg.experiment.random_seed,
        )
        elist.to_csv(edges_path)
    else:
        log.info("Reading edges from CSV: %s", edges_path)
        elist = EdgeList.read_from_csv(edges_path)

    g = build_graph_from_edges(elist).graph
    assign_node_attributes_by_incoming_weight(g)

    # Metrics and influence scores
    metrics = compute_node_metrics(g)
    scores = compute_node_influence_scores(g)

    # Optimization: select nodes to verify
    budget = cfg.experiment.verification_budget
    opt_res = solve_verification_selection(g, budget=budget)
    verified: Set[int] = opt_res.verified_nodes
    log.info("Selected %d nodes for verification (budget=%d)", len(verified), budget)

    # Game-theoretic analysis on top candidates
    top_candidates = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[: cfg.experiment.max_candidates_for_game]
    cand_nodes: List[int] = [n for n, _ in top_candidates]
    cand_scores: List[float] = [scores[n] for n in cand_nodes]
    payoff = build_payoff_from_candidates(cand_scores)
    game_sol = solve_zero_sum_game(payoff)
    log.info("Game value: %.4f", game_sol.value)

    # Monte Carlo simulation before and after
    rng = np.random.default_rng(cfg.experiment.random_seed)
    attacker_seeds = list(rng.choice(list(g.nodes), size=min(cfg.experiment.attacker_seed_count, g.number_of_nodes()), replace=False))
    mc_before = monte_carlo_spread(g, seed_nodes=attacker_seeds, verified_nodes=None, runs=cfg.experiment.num_monte_carlo_runs, seed=cfg.experiment.random_seed)
    mc_after = monte_carlo_spread(g, seed_nodes=attacker_seeds, verified_nodes=verified, runs=cfg.experiment.num_monte_carlo_runs, seed=cfg.experiment.random_seed)
    reduction_pct = 100.0 * (mc_before.avg_infected - mc_after.avg_infected) / max(1e-9, mc_before.avg_infected)
    log.info("Avg infected before: %.2f, after: %.2f, reduction: %.2f%%", mc_before.avg_infected, mc_after.avg_infected, reduction_pct)

    # Discrete-event simulation snapshot
    des = run_discrete_event(
        g,
        initial_infected=attacker_seeds,
        verified_nodes=verified,
        max_time=cfg.experiment.discrete_event_max_time,
        seed=cfg.experiment.random_seed,
    )
    log.info("DES total infected by T=%.1f: %d", cfg.experiment.discrete_event_max_time, des.total_infected)

    # Allocation models demo
    # Example: assign fact-checkers to clusters; here we create a toy cost matrix from scores
    k = min(5, len(cand_nodes))
    cost = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            # Lower cost to assign high-score checker to high-risk cluster (heuristic)
            cost[i, j] = 1.0 / (1e-3 + cand_scores[j]) + 0.01 * abs(i - j)
    assign_res = hungarian(cost)
    log.info("Hungarian assignment total cost: %.3f, pairs: %s", assign_res.total_cost, assign_res.assignment)

    # Transportation demo (balanced by construction)
    supply = np.full(k, 1.0)
    demand = np.full(k, 1.0)
    trans_res = modi_method(cost, supply, demand)
    log.info("Transportation total cost: %.3f", trans_res.total_cost)

    # Outputs and plots
    out_before = cfg.paths.results_dir / cfg.io.before_png
    out_after = cfg.paths.results_dir / cfg.io.after_png
    out_infl = cfg.paths.results_dir / cfg.io.influence_png
    out_conv = cfg.paths.results_dir / cfg.io.sim_convergence_png
    out_html = cfg.paths.results_dir / cfg.io.plotly_html
    gexf_path = cfg.paths.results_dir / cfg.io.graph_gexf_filename

    draw_graph(g, out_before, verified=None, title="Network before verification")
    draw_graph(g, out_after, verified=verified, title="Network after verification")
    plot_influence(g, scores, out_infl)
    plot_sim_convergence_series({"before": mc_before.infections_per_run, "after": mc_after.infections_per_run}, out_conv)
    plotly_interactive_graph(g, out_html, verified=verified, title="Interactive network")
    export_gexf(g, gexf_path)

    # Print summary
    print("Optimized verification set:", sorted(list(verified)))
    print(f"Misinformation reduction percentage: {reduction_pct:.2f}%")
    print("Game equilibrium (defender) strategy (first 10):", np.round(game_sol.row_mixed_strategy[:10], 3))
    print("Game equilibrium (attacker) strategy (first 10):", np.round(game_sol.col_mixed_strategy[:10], 3))
    print("Monte Carlo runs:", cfg.experiment.num_monte_carlo_runs)


if __name__ == "__main__":
    main()