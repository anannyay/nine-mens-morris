## Social Media Misinformation Containment - An Operations Research Approach

This project models and minimizes misinformation spread in social networks using Operations Research techniques. It integrates integer programming, network analysis, game theory, simulation (Monte Carlo and discrete-event), and allocation models (assignment and transportation).

### Features
- Synthetic directed network generation with weighted influence edges
- Identification of high-degree and central nodes (degree, betweenness, PageRank)
- 0–1 Integer Programming to select nodes for verification under a budget
- Zero-sum strategic game between fact-checkers and spreaders (mixed strategies)
- Monte Carlo independent-cascade propagation and SimPy-based discrete-event simulation
- Assignment (Hungarian) and Transportation (MODI) allocation demos
- Visualizations: pre/post verification graphs, influence ranking, convergence curves, Plotly interactive, and Gephi GEXF export

### Project Structure
- `models/` → optimization, game theory, allocation models
- `simulation/` → Monte Carlo and discrete-event simulation
- `network/` → graph generation and analysis
- `visualization/` → Matplotlib/Plotly plots and Gephi export
- `utils/` → configuration, data, and logging utilities
- `data/` → sample synthetic dataset (`synthetic_edges.csv`)
- `results/` → generated plots and artifacts
- `main.py` → orchestrates the complete workflow

### Setup
1. Python 3.10+ recommended
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Usage
Run end-to-end workflow and generate outputs into `results/`:
```bash
python main.py
```

Options:
- `--use-synthetic` Use an ER random graph instead of CSV
- `--budget INT` Verification budget override (default: config)
- `--mc-runs INT` Monte Carlo runs (default: config)
- `--seed INT` Random seed

Example:
```bash
python main.py --use-synthetic --budget 8 --mc-runs 300 --seed 123
```

### Outputs
- Optimized verification set and reduction percentage (stdout)
- Plots in `results/`:
  - `graph_before.png`, `graph_after.png`
  - `node_influence.png`
  - `simulation_convergence.png`
  - `graph_interactive.html`
  - `network_export.gexf` (for Gephi)

### Notes
- The IP solver uses PuLP with CBC. If CBC is unavailable on your platform, install a compatible CBC binary or use OR-Tools and adapt the solver call.
- The transportation MODI implementation is simplified for small instances; the assignment solver uses SciPy’s `linear_sum_assignment`.
