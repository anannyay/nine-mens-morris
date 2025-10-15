from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class AssignmentResult:
    total_cost: float
    assignment: List[Tuple[int, int]]  # (worker, task)


def hungarian(cost_matrix: np.ndarray) -> AssignmentResult:
    """
    Hungarian algorithm for square/rectangular matrices.
    Returns minimal assignment. Implementation uses a well-known O(n^3) method.
    """
    from scipy.optimize import linear_sum_assignment  # fallback to scipy for robustness

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    total = float(cost_matrix[row_ind, col_ind].sum())
    assignment = list(zip(row_ind.tolist(), col_ind.tolist()))
    return AssignmentResult(total_cost=total, assignment=assignment)


@dataclass
class TransportationResult:
    total_cost: float
    flow: np.ndarray


def modi_method(cost: np.ndarray, supply: np.ndarray, demand: np.ndarray) -> TransportationResult:
    """
    MODI (u-v) method with Northwest Corner initial feasible solution.
    This is a simplified implementation suitable for small instances.
    """
    cost = cost.astype(float)
    m, n = cost.shape
    supply = supply.astype(float).copy()
    demand = demand.astype(float).copy()

    # Initial feasible solution via Northwest Corner
    x = np.zeros_like(cost)
    i, j = 0, 0
    while i < m and j < n:
        amount = min(supply[i], demand[j])
        x[i, j] = amount
        supply[i] -= amount
        demand[j] -= amount
        if abs(supply[i]) < 1e-9:
            i += 1
        if abs(demand[j]) < 1e-9:
            j += 1

    def compute_potentials(basis_mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        # Solve u+v=c on basic cells
        u = np.full(m, np.nan)
        v = np.full(n, np.nan)
        u[0] = 0.0
        changed = True
        while changed:
            changed = False
            for ii in range(m):
                for jj in range(n):
                    if basis_mask[ii, jj]:
                        if not np.isnan(u[ii]) and np.isnan(v[jj]):
                            v[jj] = cost[ii, jj] - u[ii]
                            changed = True
                        elif np.isnan(u[ii]) and not np.isnan(v[jj]):
                            u[ii] = cost[ii, jj] - v[jj]
                            changed = True
        # Replace nans with zeros for stability
        u = np.nan_to_num(u, nan=0.0)
        v = np.nan_to_num(v, nan=0.0)
        return u, v

    def improve_solution(x: np.ndarray) -> np.ndarray:
        basis = x > 1e-12
        u, v = compute_potentials(basis)
        # Reduced costs
        reduced = cost - (u[:, None] + v[None, :])
        # Optimal if all non-basic reduced costs are >= 0 (within tolerance)
        non_basic_mask = ~basis
        if np.all(reduced[non_basic_mask] >= -1e-12):
            return x
        # Find most negative reduced cost among non-basic cells
        min_val = np.inf
        pivot = (None, None)
        for ii in range(m):
            for jj in range(n):
                if not basis[ii, jj] and reduced[ii, jj] < min_val:
                    min_val = reduced[ii, jj]
                    pivot = (ii, jj)

        pi, pj = pivot
        # Build a cycle path; simplified for small sizes by DFS over basis graph
        # For brevity, we use a very basic cycle finder that may be O(m^2 n^2) but fine for small matrices
        def find_cycle():
            # construct row/col adjacency among basic cells plus pivot
            rows = {r: [c for c in range(n) if basis[r, c] or c == pj] for r in range(m)}
            cols = {c: [r for r in range(m) if basis[r, c] or r == pi] for c in range(n)}
            # DFS alternating row->col->row to find cycle
            stack = [(pi, pj, 0)]  # 0 means next move is along row
            visited = set()
            parent = {}
            while stack:
                r, c, state = stack.pop()
                if (r, c, state) in visited:
                    continue
                visited.add((r, c, state))
                if r == pi and c == pj and (r, c) != (pi, pj):
                    break
                if state == 0:
                    for cc in rows[r]:
                        if cc != c:
                            parent[(r, cc, 1)] = (r, c, state)
                            stack.append((r, cc, 1))
                else:
                    for rr in cols[c]:
                        if rr != r:
                            parent[(rr, c, 0)] = (r, c, state)
                            stack.append((rr, c, 0))
            # Reconstruct a simple 4-cycle around pivot if exists; fallback: no improvement
            # For simplicity in this teaching implementation, attempt a rectangle using another basic cell in same row and column
            for c2 in range(n):
                if c2 != pj and basis[pi, c2]:
                    for r2 in range(m):
                        if r2 != pi and basis[r2, pj] and basis[r2, c2]:
                            return [(pi, pj), (pi, c2), (r2, c2), (r2, pj)]
            return None

        cycle = find_cycle()
        if cycle is None:
            return x
        minus_cells = cycle[1::2]
        theta = min(x[i, j] for i, j in minus_cells)
        for k, (i2, j2) in enumerate(cycle):
            if k % 2 == 0:
                x[i2, j2] += theta
            else:
                x[i2, j2] -= theta
        return x

    # Iterate improvements up to a small limit
    for _ in range(20):
        x_new = improve_solution(x.copy())
        if np.allclose(x_new, x):
            break
        x = x_new

    total = float((x * cost).sum())
    return TransportationResult(total_cost=total, flow=x)
