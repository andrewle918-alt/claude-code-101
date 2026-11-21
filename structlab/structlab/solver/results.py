"""Result data classes returned by ``solve(model)``. All values SI.

SIGN CONVENTIONS (also in the README / in-app help)
  Axial N   : tension positive.
  Shear V   : positive when it tends to rotate the member segment clockwise
              (upward on the left face of a segment).
  Moment M  : positive = sagging (compression on top, tension on the bottom,
              for a member whose local y axis points "up").
  Displacements/reactions: global axes, +x right, +y up, rotation CCW positive.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class MemberResult:
    id: int
    kind: str
    node_i: int
    node_j: int
    length: float
    N_i: float                 # axial force at end i (tension +), N
    N_j: float                 # axial force at end j
    V_i: float                 # shear at end i, N
    V_j: float
    M_i: float                 # bending moment at end i (sagging +), N*m
    M_j: float
    axial_stress: float        # average N/A, Pa
    max_tension_stress: float  # max over the member incl. bending, Pa (0 if none)
    max_compression_stress: float   # most negative stress (<= 0), Pa
    strain: float              # total axial strain = elongation / L
    elongation: float          # change of length, m
    fos: float                 # factor of safety against yield (inf if unstressed)
    state: str                 # "tension" | "compression" | "zero"
    status: str                # "OK" | "yields" | "tension in compression-only material"
    material: str
    # data needed to rebuild diagrams exactly (local axes)
    u_local: tuple[float, ...]            # [u_i, v_i, th_i, u_j, v_j, th_j]
    loads_local: tuple[float, float, float, float]   # wx1, wx2, wy1, wy2 (N/m)
    E: float = 0.0
    A: float = 0.0
    Iz: float = 0.0

    @property
    def axial(self) -> float:
        """Representative axial force (average of the two ends)."""
        return 0.5 * (self.N_i + self.N_j)


@dataclass
class MemberDiagram:
    """Internal-force and deflection curves along one member (local axes)."""

    x: np.ndarray
    N: np.ndarray
    V: np.ndarray
    M: np.ndarray
    theta: np.ndarray     # rotation, rad
    v: np.ndarray         # transverse deflection (local +y), m


@dataclass
class Diagnostics:
    n_nodes: int = 0
    n_members: int = 0
    n_dof: int = 0                       # active DOFs in the system
    n_restraints: int = 0                # restrained active DOFs
    degree_indeterminacy: int = 0        # unknowns + restraints - equations
    smallest_scaled_eigenvalue: float | None = None
    stable: bool = True
    warnings: list[str] = field(default_factory=list)
    # global equilibrium: sum of applied loads + reactions should be zero
    equilibrium_ok: bool = True
    equilibrium_residual: tuple[float, float, float] = (0.0, 0.0, 0.0)   # (Fx, Fy, M_origin)
    equilibrium_tolerance: tuple[float, float, float] = (0.0, 0.0, 0.0)

    @property
    def determinacy(self) -> str:
        d = self.degree_indeterminacy
        if d == 0:
            return "statically determinate"
        if d > 0:
            return f"statically indeterminate to degree {d}"
        return f"deficient by {-d} (necessary-condition count says mechanism)"


@dataclass
class Results:
    model_name: str
    load_factor: float
    node_ids: list[int]
    displacements: dict[int, tuple[float, float, float]]    # node id -> (ux, uy, rz)
    reactions: dict[int, tuple[float, float, float]]        # node id -> (Rx, Ry, Mz)
    members: dict[int, MemberResult]
    diagnostics: Diagnostics
    max_displacement: float = 0.0        # largest translation magnitude, m

    def displacement(self, node_id: int) -> tuple[float, float, float]:
        return self.displacements[node_id]

    def reaction(self, node_id: int) -> tuple[float, float, float]:
        return self.reactions[node_id]

    def total_reaction(self) -> tuple[float, float, float]:
        rx = sum(r[0] for r in self.reactions.values())
        ry = sum(r[1] for r in self.reactions.values())
        mz = sum(r[2] for r in self.reactions.values())
        return rx, ry, mz

    def summary(self, system: str = "SI") -> str:
        """Plain-text report (what the CLI prints)."""
        from .. import units as U

        def f(q: str, v: float) -> float:
            return U.from_si(q, v, system)

        ul = lambda q: U.unit_label(q, system)
        d = self.diagnostics
        lines = [f"Results for '{self.model_name}' (load factor {self.load_factor:g}, units {system})",
                 f"  {d.n_nodes} nodes, {d.n_members} members, {d.n_dof} DOFs, "
                 f"{d.n_restraints} restraints -> {d.determinacy}"]
        eq = "OK" if d.equilibrium_ok else "FAILED"
        lines.append(f"  Global equilibrium check: {eq}  (residual Fx={d.equilibrium_residual[0]:.3g} N, "
                     f"Fy={d.equilibrium_residual[1]:.3g} N, M={d.equilibrium_residual[2]:.3g} N*m)")
        for w in d.warnings:
            lines.append(f"  WARNING: {w}")
        lines.append("")
        lines.append(f"Reactions [{ul('force')}, {ul('moment')}]")
        for nid, (rx, ry, mz) in self.reactions.items():
            lines.append(f"  node {nid:>3}: Rx={f('force', rx):>12.4f}  Ry={f('force', ry):>12.4f}  "
                         f"Mz={f('moment', mz):>12.4f}")
        lines.append("")
        lines.append(f"Displacements [{ul('displacement')}, rad]")
        for nid, (ux, uy, rz) in self.displacements.items():
            lines.append(f"  node {nid:>3}: ux={f('displacement', ux):>12.5f}  "
                         f"uy={f('displacement', uy):>12.5f}  rz={rz:>12.6f}")
        lines.append(f"  largest translation: {f('displacement', self.max_displacement):.5f} {ul('displacement')}")
        lines.append("")
        lines.append(f"Members  (tension +) [{ul('force')}, {ul('stress')}]")
        lines.append("   id kind    length      N_i      N_j     V_i     M_i     max stress  FoS    status")
        for m in self.members.values():
            smax = max(abs(m.max_tension_stress), abs(m.max_compression_stress))
            fos = "inf" if math.isinf(m.fos) else f"{m.fos:.2f}"
            lines.append(
                f"  {m.id:>3} {m.kind:<6} {f('length', m.length):>8.4f} {f('force', m.N_i):>9.3f} "
                f"{f('force', m.N_j):>8.3f} {f('force', m.V_i):>7.3f} {f('moment', m.M_i):>7.3f} "
                f"{f('stress', smax):>12.3f} {fos:>5}  {m.status}  ({m.state})")
        return "\n".join(lines)
