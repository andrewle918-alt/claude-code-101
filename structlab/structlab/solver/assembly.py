"""Direct stiffness assembly for 2D models.

The big picture (read this first if you are learning the method):

  1. Every node has 3 DOFs: ux, uy, rz.  DOF number of (node row n, component k) is 3*n + k.
  2. Each member gives an element stiffness matrix in its LOCAL axes.
  3. We rotate it to GLOBAL axes:   k_global = T^T k_local T
  4. We "add it in" to the big matrix K at the rows/columns of the element's DOFs.
  5. Loads become a vector F (nodal loads + equivalent nodal loads of member loads).
  6. Solve  K u = F  after removing the restrained DOFs (done in api.py).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from ..core.member import FRAME, TRUSS
from ..core.model import Model
from ..materials.library import MaterialLibrary
from ..materials.sections import section_from_spec
from .elements import beam2d, truss
from .errors import ModelError, UnsupportedError


@dataclass
class MemberData:
    """Everything the solver needs about one member (SI units)."""

    id: int
    kind: str
    node_i: int
    node_j: int
    row_i: int                # node row (index into model.nodes)
    row_j: int
    L: float
    c: float                  # cos of member angle
    s: float                  # sin of member angle
    E: float
    A: float
    Iz: float
    c_y: float
    rho: float
    alpha: float
    material: str
    w_local: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])  # wx1, wx2, wy1, wy2
    delta_t: float = 0.0
    dofs: list[int] = field(default_factory=list)
    f_eq_local: np.ndarray | None = None       # equivalent nodal load, local axes

    @property
    def is_frame(self) -> bool:
        return self.kind == FRAME


@dataclass
class System:
    """The assembled global system."""

    n_dof: int
    active: np.ndarray          # bool mask: True where the DOF takes part in the analysis
    K: np.ndarray               # global stiffness (without springs), n_dof x n_dof
    F: np.ndarray               # global load vector (loads * load_factor)
    members: list[MemberData]
    warnings: list[str]


def dof_index(row: int, k: int) -> int:
    return 3 * row + k


def prepare_members(model: Model, library: MaterialLibrary, load_factor: float) -> list[MemberData]:
    """Turn model Members into MemberData: lengths, angles, material/section values, member loads."""
    rows = {n.id: r for r, n in enumerate(model.nodes)}
    problems: list[str] = []
    out: list[MemberData] = []
    by_id: dict[int, MemberData] = {}

    for m in model.members:
        if m.kind not in (TRUSS, FRAME):
            raise UnsupportedError(
                f"Member {m.id} is a '{m.kind}'. Cables (tension-only) are planned for a later phase "
                "and rigid links are handled by the machine solver (Phase 7).")
        if m.release_i or m.release_j:
            raise UnsupportedError(
                f"Member {m.id} has an end release. Releases (pinned ends in frames) arrive in Phase 4.")
        if m.section is None:
            problems.append(f"Member {m.id} has no cross-section assigned.")
            continue
        if m.material not in library:
            problems.append(f"Member {m.id} uses unknown material {m.material!r}.")
            continue
        try:
            sec = section_from_spec(m.section)
        except (KeyError, ValueError, TypeError) as exc:
            problems.append(f"Member {m.id} has an invalid section: {exc}")
            continue
        mat = library.get(m.material)
        a, b = model.node(m.i), model.node(m.j)
        L = math.dist(a.xyz, b.xyz)
        md = MemberData(
            id=m.id, kind=m.kind, node_i=m.i, node_j=m.j, row_i=rows[m.i], row_j=rows[m.j], L=L,
            c=(b.x - a.x) / L, s=(b.y - a.y) / L, E=mat.E, A=sec.A, Iz=sec.Iz, c_y=sec.c_y,
            rho=mat.density, alpha=mat.cte, material=m.material)
        if m.kind == FRAME:
            md.dofs = [dof_index(md.row_i, k) for k in range(3)] + [dof_index(md.row_j, k) for k in range(3)]
        else:
            md.dofs = [dof_index(md.row_i, 0), dof_index(md.row_i, 1),
                       dof_index(md.row_j, 0), dof_index(md.row_j, 1)]
        out.append(md)
        by_id[m.id] = md
    if problems:
        raise ModelError(problems)

    def add_global_load(md: MemberData, w1: tuple, w2: tuple, frame: str) -> None:
        """Accumulate a linear load (global or local components) into the member's LOCAL loads."""
        if abs(w1[2]) > 0 or abs(w2[2]) > 0:
            raise ModelError(f"Member {md.id} has a z-direction load in a 2D model.")
        if frame == "global":
            conv = lambda w: (md.c * w[0] + md.s * w[1], -md.s * w[0] + md.c * w[1])
        else:
            conv = lambda w: (w[0], w[1])
        (x1, y1), (x2, y2) = conv(w1), conv(w2)
        md.w_local[0] += x1 * load_factor
        md.w_local[1] += x2 * load_factor
        md.w_local[2] += y1 * load_factor
        md.w_local[3] += y2 * load_factor

    for ld in model.member_loads:
        add_global_load(by_id[ld.member], ld.w_start, ld.w_end, ld.frame)
    if model.self_weight:
        for md in out:
            w = tuple(md.rho * md.A * g for g in model.gravity)   # weight per length = rho*A*g  (N/m)
            add_global_load(md, w, w, "global")
    for tl in model.thermal_loads:
        for md in out:
            if tl.member is None or tl.member == md.id:
                md.delta_t += tl.delta_t * load_factor
    return out


def active_dof_mask(model: Model, members: list[MemberData]) -> np.ndarray:
    """ux, uy are always active. rz is active only at nodes touched by a FRAME member
    (a node joining only pin-jointed bars has no rotational stiffness at all)."""
    mask = np.zeros(3 * len(model.nodes), dtype=bool)
    mask[0::3] = True
    mask[1::3] = True
    for md in members:
        if md.is_frame:
            mask[dof_index(md.row_i, 2)] = True
            mask[dof_index(md.row_j, 2)] = True
    return mask


def assemble(model: Model, members: list[MemberData], load_factor: float) -> System:
    n = 3 * len(model.nodes)
    K = np.zeros((n, n))
    F = np.zeros(n)
    warnings: list[str] = []
    active = active_dof_mask(model, members)
    rows = {nd.id: r for r, nd in enumerate(model.nodes)}

    for md in members:
        wx1, wx2, wy1, wy2 = md.w_local
        if md.is_frame:
            k_loc = beam2d.local_stiffness(md.E, md.A, md.Iz, md.L)
            T = beam2d.transformation(md.c, md.s)
            f_eq = beam2d.equivalent_load_local(md.L, wx1, wx2, wy1, wy2)
            if md.delta_t:
                f_eq = f_eq + beam2d.thermal_load_local(md.E, md.A, md.alpha, md.delta_t)
        else:
            k_loc = truss.local_stiffness(md.E, md.A, md.L)
            T = truss.transformation(md.c, md.s)
            f_eq = truss.lumped_load_local(md.L, wx1, wx2, wy1, wy2)
            if md.delta_t:
                f_eq = f_eq + truss.thermal_load_local(md.E, md.A, md.alpha, md.delta_t)
        md.f_eq_local = f_eq

        k_glob = T.T @ k_loc @ T          # k_global = T^T k_local T
        K[np.ix_(md.dofs, md.dofs)] += k_glob      # "add into" the rows/columns of this element
        F[md.dofs] += T.T @ f_eq          # equivalent nodal loads, rotated to global axes

    for ld in model.nodal_loads:
        r = rows[ld.node]
        if abs(ld.force[2]) > 0 or abs(ld.moment[0]) > 0 or abs(ld.moment[1]) > 0:
            raise ModelError(f"Load at node {ld.node} has out-of-plane components in a 2D model.")
        F[dof_index(r, 0)] += ld.force[0] * load_factor
        F[dof_index(r, 1)] += ld.force[1] * load_factor
        if ld.moment[2] != 0.0:
            if not active[dof_index(r, 2)]:
                raise ModelError(
                    f"A moment is applied at node {ld.node}, which joins only pin-jointed truss bars. "
                    "A pin cannot transmit a moment: connect a frame member there or remove the moment.")
            F[dof_index(r, 2)] += ld.moment[2] * load_factor
    return System(n, active, K, F, members, warnings)
