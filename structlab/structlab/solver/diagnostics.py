"""Stability, indeterminacy and equilibrium checks.

These exist so the solver never silently returns garbage: every solve either
raises a clear error or returns results that passed these checks.
"""
from __future__ import annotations

import numpy as np

from ..core.model import Model
from .assembly import MemberData

# Above this many free DOFs the dense eigen-analysis is replaced by a sparse one.
DENSE_LIMIT = 1500
# A *scaled* stiffness eigenvalue below this means "moves without resisting".
MECHANISM_TOL = 1e-9


def degree_of_indeterminacy(members: list[MemberData], n_active: int, n_restraints: int) -> int:
    """Degree of static indeterminacy  d = (member force unknowns) + (restraints) - (equations).

    Pin-jointed bar: 1 unknown (axial force). Frame member: 3 unknowns (N, V, M).
    Equations: one per active DOF (2 per pin joint, 3 per rigid joint).
    For a plane truss this reduces to the familiar  m + r - 2j.
    d < 0 means a mechanism for sure; d >= 0 does NOT guarantee stability (checked separately).
    """
    unknowns = sum(3 if md.is_frame else 1 for md in members)
    return unknowns + n_restraints - n_active


def find_mechanisms(K_ff: np.ndarray, free: np.ndarray, node_of_dof: dict[int, int]
                    ) -> tuple[float, list[int], int]:
    """Look for motions that cost no strain energy.

    Returns (smallest scaled eigenvalue, node ids involved, number of mechanism modes).
    K is symmetrically scaled by its diagonal first (Jacobi scaling) so translations and
    rotations, which have very different units, are compared fairly.
    """
    n = K_ff.shape[0]
    if n == 0:
        return 1.0, [], 0
    diag = np.diag(K_ff).copy()
    dead = diag <= 0
    scale = np.where(dead, 1.0, np.sqrt(np.where(dead, 1.0, diag)))
    Ks = K_ff / scale[:, None] / scale[None, :]

    if n <= DENSE_LIMIT:
        w, V = np.linalg.eigh(Ks)
    else:
        from scipy.sparse import csc_matrix
        from scipy.sparse.linalg import eigsh
        w, V = eigsh(csc_matrix(Ks), k=min(8, n - 2), sigma=-1e-3, which="LM")
    null_idx = [i for i in range(len(w)) if w[i] < MECHANISM_TOL]
    nodes: set[int] = set()
    for i in null_idx:
        vec = np.abs(V[:, i])
        for local in np.flatnonzero(vec > 0.1 * vec.max()):
            nodes.add(node_of_dof[int(free[local])])
    for local in np.flatnonzero(dead):
        nodes.add(node_of_dof[int(free[local])])
    return float(w.min()), sorted(nodes), max(len(null_idx), int(dead.sum()))


def applied_resultants(model: Model, members: list[MemberData], load_factor: float
                       ) -> tuple[float, float, float]:
    """Total applied force (Fx, Fy) and moment about the global origin, computed
    DIRECTLY from the loads (not from the equivalent nodal loads), so the
    equilibrium check is an independent test of the solver.
    """
    Fx = Fy = M0 = 0.0
    for ld in model.nodal_loads:
        n = model.node(ld.node)
        fx, fy = ld.force[0] * load_factor, ld.force[1] * load_factor
        Fx += fx
        Fy += fy
        M0 += n.x * fy - n.y * fx + ld.moment[2] * load_factor
    for md in members:
        wx1, wx2, wy1, wy2 = md.w_local
        L = md.L
        # linear load resultants in local axes; transverse load moment about node i:
        #   integral s*w(s) ds = L^2 (w1/6 + w2/3)
        fxl = L * (wx1 + wx2) / 2
        fyl = L * (wy1 + wy2) / 2
        mzl = L**2 * (wy1 / 6 + wy2 / 3)
        fx = md.c * fxl - md.s * fyl           # local -> global rotation
        fy = md.s * fxl + md.c * fyl
        a = model.node(md.node_i)
        Fx += fx
        Fy += fy
        M0 += a.x * fy - a.y * fx + mzl
    return Fx, Fy, M0


def check_equilibrium(applied: tuple[float, float, float],
                      reactions: list[tuple[float, float, float, float, float]],
                      rtol: float = 1e-6) -> tuple[bool, tuple[float, float, float], tuple[float, float, float]]:
    """Global equilibrium: applied loads + support reactions must sum to zero.

    ``reactions`` is a list of (x, y, Rx, Ry, Mz) with the node position in metres.
    Returns (ok, residual (Fx, Fy, M0), tolerance).
    """
    Fx, Fy, M0 = applied
    sx = abs(Fx) + sum(abs(r[2]) for r in reactions)
    sy = abs(Fy) + sum(abs(r[3]) for r in reactions)
    sm = abs(M0) + sum(abs(r[0] * r[3]) + abs(r[1] * r[2]) + abs(r[4]) for r in reactions)
    rx = Fx + sum(r[2] for r in reactions)
    ry = Fy + sum(r[3] for r in reactions)
    rm = M0 + sum(r[0] * r[3] - r[1] * r[2] + r[4] for r in reactions)
    tol = (rtol * max(sx, 1.0), rtol * max(sy, 1.0), rtol * max(sm, 1.0))
    ok = abs(rx) <= tol[0] and abs(ry) <= tol[1] and abs(rm) <= tol[2]
    return ok, (rx, ry, rm), tol
