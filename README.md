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
- `--fakenewsnet-root PATH` Build graph from FakeNewsNet root directory
- `--fakenewsnet-alpha FLOAT` Map interaction counts to edge probabilities (default 0.05)
- `--fakenewsnet-news-limit INT` Limit processed news items (subset)
- `--fakenewsnet-tweets-limit INT` Limit tweets per news (subset)
- `--budget INT` Verification budget override (default: config)
- `--mc-runs INT` Monte Carlo runs (default: config)
- `--seed INT` Random seed

Example:
```bash
python main.py --use-synthetic --budget 8 --mc-runs 300 --seed 123
```

Using FakeNewsNet (example directory structure under `PATH`):
```bash
python main.py --fakenewsnet-root /data/FakeNewsNet --fakenewsnet-alpha 0.05 \
  --fakenewsnet-news-limit 200 --fakenewsnet-tweets-limit 500 --budget 10 --mc-runs 300
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
 - FakeNewsNet loader scans `{politifact,gossipcop}/{fake,real}/*/tweets/*.json`. It extracts user-to-user edges from retweets, replies, and mentions. Edge probabilities are mapped from interaction counts via `p = 1 - exp(-alpha * count)` and clipped to `[1e-4, 0.95]`.
