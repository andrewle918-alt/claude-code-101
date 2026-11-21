"""Public solver entry point:  ``results = solve(model)``.

Steps (each one is a short, commented block below):
  1. validate the model          5. add springs, apply support rotations
  2. prepare members             6. partition into free / restrained DOFs and solve
  3. assemble K and F            7. reactions  R = K u - F
  4. count DOFs, indeterminacy   8. recover member forces, run equilibrium check
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.model import Model
from ..materials.library import MaterialLibrary, default_library
from . import assembly, diagnostics, recovery
from .errors import InstabilityError, ModelError, SolverError, UnsupportedError
from .results import Diagnostics, Results

# 2D DOF k (0 ux, 1 uy, 2 rz)  ->  index in the Support tuples (ux, uy, uz, rx, ry, rz)
_SUPPORT_INDEX = (0, 1, 5)
# Warn when displacements exceed this fraction of the structure's overall size.
LARGE_DISPLACEMENT_FRACTION = 0.01


@dataclass
class AnalysisOptions:
    """Switches for one analysis run."""

    load_factor: float = 1.0       # multiplies all applied loads (load-scaling slider)


def solve(model: Model, options: AnalysisOptions | None = None,
          library: MaterialLibrary | None = None) -> Results:
    """Solve a 2D truss / beam / frame model by the direct stiffness method.

    Raises ``ModelError`` for bad data, ``InstabilityError`` for mechanisms or
    insufficient supports, ``UnsupportedError`` for features not built yet.
    """
    options = options or AnalysisOptions()
    library = library or default_library()
    lf = options.load_factor

    # 1 ---- validate ------------------------------------------------------------------
    if model.dimension != 2:
        raise UnsupportedError("3D analysis arrives in Phase 6; this solver handles 2D models.")
    problems = model.validate()
    if problems:
        raise ModelError(problems)
    if not model.members:
        raise ModelError("The model has no members.")

    # 2-3 --- members and assembly ---------------------------------------------------------
    members = assembly.prepare_members(model, library, lf)
    sysm = assembly.assemble(model, members, lf)
    n = sysm.n_dof
    rows = {nd.id: r for r, nd in enumerate(model.nodes)}
    node_of_dof = {d: model.nodes[d // 3].id for d in range(n)}
    warnings = list(sysm.warnings)

    # 4 ---- support data per DOF -----------------------------------------------------------
    fixed = np.zeros(n, dtype=bool)
    prescribed = np.zeros(n)
    spring = np.zeros(n)
    Lam = np.eye(n)                      # rotation of DOFs to support axes (inclined rollers)
    rotated = False
    for s in model.supports:
        r = rows[s.node]
        if s.angle_deg:
            th = np.radians(s.angle_deg)
            c, sn = np.cos(th), np.sin(th)
            Lam[3 * r:3 * r + 2, 3 * r:3 * r + 2] = [[c, sn], [-sn, c]]   # u' = R u
            rotated = True
        for k in range(3):
            d = 3 * r + k
            si = _SUPPORT_INDEX[k]
            if not sysm.active[d]:
                continue                        # inactive rz at pin-only nodes: nothing to restrain
            if s.fixed[si]:
                fixed[d] = True
                prescribed[d] = s.settlement[si]
            if s.spring[si]:
                spring[d] += s.spring[si]

    K, F = sysm.K, sysm.F
    if rotated:
        K = Lam @ K @ Lam.T              # K' = L K L^T   (stiffness in the support axes)
        F = Lam @ F
    K_solve = K.copy()
    K_solve[np.diag_indices(n)] += spring    # elastic supports add k to the diagonal

    active = sysm.active
    free = np.flatnonzero(active & ~fixed)
    cons = np.flatnonzero(active & fixed)

    diag = Diagnostics(
        n_nodes=len(model.nodes), n_members=len(members), n_dof=int(active.sum()),
        n_restraints=int(len(cons)),
        degree_indeterminacy=diagnostics.degree_of_indeterminacy(members, int(active.sum()), len(cons)),
        warnings=warnings)

    # 5 ---- stability (mechanisms / supports) ---------------------------------------------------
    # (With every DOF restrained there is nothing to solve for, but reactions still follow.)
    K_ff = K_solve[np.ix_(free, free)]
    lam_min, bad_nodes, n_modes = diagnostics.find_mechanisms(K_ff, free, node_of_dof)
    diag.smallest_scaled_eigenvalue = lam_min
    if n_modes > 0:
        diag.stable = False
        hint = ""
        if diag.n_restraints < 3 and not np.any(spring):
            hint = (" The supports restrain only "
                    f"{diag.n_restraints} DOF(s); a plane structure needs at least 3 independent "
                    "restraints to prevent rigid-body motion.")
        elif diag.degree_indeterminacy < 0:
            hint = (f" The member/support count is short by {-diag.degree_indeterminacy}: "
                    "add members (e.g. diagonal bracing) or supports.")
        raise InstabilityError(
            f"Structure is unstable: {n_modes} independent motion(s) can occur without any member "
            f"resisting (nodes involved: {bad_nodes}).{hint} "
            "Typical causes: a missing diagonal in a truss panel, a node connected to nothing, "
            "or too few/badly placed supports.", diag)

    # 6 ---- solve  K_ff u_f = F_f - K_fc u_c ---------------------------------------------------
    u = np.zeros(n)
    u[cons] = prescribed[cons]
    rhs = F[free] - K_solve[np.ix_(free, cons)] @ u[cons]
    try:
        if len(free) == 0:
            pass
        elif len(free) > diagnostics.DENSE_LIMIT:
            from scipy.sparse import csc_matrix
            from scipy.sparse.linalg import spsolve
            u[free] = spsolve(csc_matrix(K_ff), rhs)
        else:
            u[free] = np.linalg.solve(K_ff, rhs)
    except np.linalg.LinAlgError as exc:
        diag.stable = False
        raise InstabilityError("The stiffness matrix is singular: " + str(exc), diag) from exc
    if not np.all(np.isfinite(u)):
        diag.stable = False
        raise InstabilityError("The solution contains non-finite numbers; the model is ill-conditioned.", diag)

    # 7 ---- reactions  R = K u - F  (K without springs, so spring DOFs show the spring force) ------
    R = K @ u - F
    # Free, spring-less DOFs must have ~zero residual: this is a solution-accuracy check.
    no_support = active & ~fixed & (spring == 0)
    scale = max(1.0, float(np.max(np.abs(F))) if n else 1.0)
    if np.any(np.abs(R[no_support]) > 1e-6 * scale + 1e-6 * np.abs(K @ u)[no_support]):
        warnings.append("Large residual at unrestrained DOFs: the linear solve may be inaccurate.")
    u_glob = Lam.T @ u if rotated else u            # back to global axes
    R_glob = Lam.T @ R if rotated else R

    reactions: dict[int, tuple[float, float, float]] = {}
    for s in model.supports:
        r = rows[s.node]
        comp = []
        # With an inclined support the reaction lies along the rotated axes, so after rotating
        # back to global axes BOTH translation components may be non-zero even though only one
        # rotated DOF is restrained: report both whenever either translation is restrained.
        xy_supported = any((fixed[3 * r + k] or spring[3 * r + k] != 0) for k in (0, 1))
        for k in range(3):
            d = 3 * r + k
            if k < 2:
                has = xy_supported
            else:
                has = bool(fixed[d] or spring[d] != 0)
            comp.append(float(R_glob[d]) if has and active[d] else 0.0)
        if any(comp) or any(s.fixed):
            prev = reactions.get(s.node, (0.0, 0.0, 0.0))
            reactions[s.node] = tuple(p + c for p, c in zip(prev, comp))

    # 8 ---- member results and global equilibrium ------------------------------------------------
    member_results = {md.id: recovery.recover_member(md, u_glob, library, warnings) for md in members}

    applied = diagnostics.applied_resultants(model, members, lf)
    react_list = [(model.node(nid).x, model.node(nid).y, rx, ry, mz) for nid, (rx, ry, mz) in reactions.items()]
    ok, resid, tol = diagnostics.check_equilibrium(applied, react_list)
    diag.equilibrium_ok, diag.equilibrium_residual, diag.equilibrium_tolerance = ok, resid, tol
    if not ok:
        warnings.append(
            "GLOBAL EQUILIBRIUM CHECK FAILED: loads and reactions do not balance "
            f"(residual Fx={resid[0]:.3g} N, Fy={resid[1]:.3g} N, M={resid[2]:.3g} N*m). "
            "Do not trust these results.")

    displacements = {nd.id: (float(u_glob[3 * r]), float(u_glob[3 * r + 1]), float(u_glob[3 * r + 2]))
                     for r, nd in enumerate(model.nodes)}
    max_disp = max((float(np.hypot(a, b)) for a, b, _ in displacements.values()), default=0.0)

    # small-displacement validity warning (linear theory assumes tiny displacements)
    xs = [nd.x for nd in model.nodes]
    ys = [nd.y for nd in model.nodes]
    size = max(max(xs) - min(xs), max(ys) - min(ys), 1e-12)
    if max_disp > LARGE_DISPLACEMENT_FRACTION * size:
        warnings.append(
            f"Largest displacement is {100 * max_disp / size:.1f}% of the structure size. Linear "
            "small-displacement theory may be inaccurate here (geometry changes are ignored).")

    return Results(model_name=model.name, load_factor=lf, node_ids=[nd.id for nd in model.nodes],
                   displacements=displacements, reactions=reactions, members=member_results,
                   diagnostics=diag, max_displacement=max_disp)
