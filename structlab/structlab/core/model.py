"""Model: the complete, plain-data description of a structure.

No GUI imports, no solver imports.  A Model can be built in a script, saved to
JSON, loaded back, and handed to ``solver.solve(model)``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .loads import MemberLoad, NodalLoad, ThermalLoad
from .member import MEMBER_KINDS, Member
from .node import Node
from .supports import Support

FORMAT_VERSION = 1


@dataclass
class Model:
    name: str = "Untitled"
    dimension: int = 2                      # 2 or 3
    nodes: list[Node] = field(default_factory=list)
    members: list[Member] = field(default_factory=list)
    supports: list[Support] = field(default_factory=list)
    nodal_loads: list[NodalLoad] = field(default_factory=list)
    member_loads: list[MemberLoad] = field(default_factory=list)
    thermal_loads: list[ThermalLoad] = field(default_factory=list)
    self_weight: bool = False
    gravity: tuple[float, float, float] = (0.0, -9.81, 0.0)   # m/s^2
    display_units: str = "SI"               # "SI" or "US" (display only)
    notes: str = ""

    # ------------------------------------------------------------------ build
    def _next_id(self, items) -> int:
        return max((it.id for it in items), default=0) + 1

    def add_node(self, x: float, y: float, z: float = 0.0) -> Node:
        node = Node(self._next_id(self.nodes), float(x), float(y), float(z))
        self.nodes.append(node)
        return node

    def add_member(self, i: int, j: int, **kwargs) -> Member:
        member = Member(self._next_id(self.members), i, j, **kwargs)
        self.members.append(member)
        return member

    def add_support(self, support: Support) -> Support:
        self.supports.append(support)
        return support

    def add_nodal_load(self, load: NodalLoad) -> NodalLoad:
        self.nodal_loads.append(load)
        return load

    def add_member_load(self, load: MemberLoad) -> MemberLoad:
        self.member_loads.append(load)
        return load

    # ----------------------------------------------------------------- lookup
    def node(self, node_id: int) -> Node:
        for n in self.nodes:
            if n.id == node_id:
                return n
        raise KeyError(f"No node with id {node_id}")

    def member(self, member_id: int) -> Member:
        for m in self.members:
            if m.id == member_id:
                return m
        raise KeyError(f"No member with id {member_id}")

    def member_length(self, member: Member) -> float:
        a, b = self.node(member.i), self.node(member.j)
        return math.dist(a.xyz, b.xyz)

    # --------------------------------------------------------------- validate
    def validate(self) -> list[str]:
        """Return a list of plain-language problems (empty list = looks OK).

        This checks data consistency only; the solver separately checks
        stability (mechanisms, singular stiffness) and equilibrium.
        """
        problems: list[str] = []
        if self.dimension not in (2, 3):
            problems.append(f"dimension must be 2 or 3, not {self.dimension}.")

        node_ids = [n.id for n in self.nodes]
        if len(set(node_ids)) != len(node_ids):
            problems.append("Duplicate node ids.")
        member_ids = [m.id for m in self.members]
        if len(set(member_ids)) != len(member_ids):
            problems.append("Duplicate member ids.")
        nid = set(node_ids)
        mid = set(member_ids)

        if self.dimension == 2:
            for n in self.nodes:
                if n.z != 0.0:
                    problems.append(f"Node {n.id} has z != 0 in a 2D model.")

        for m in self.members:
            if m.i not in nid or m.j not in nid:
                problems.append(f"Member {m.id} refers to a missing node.")
                continue
            if m.i == m.j:
                problems.append(f"Member {m.id} connects node {m.i} to itself.")
            elif self.member_length(m) < 1e-9:
                problems.append(f"Member {m.id} has zero length (nodes {m.i} and {m.j} coincide).")
            if m.kind not in MEMBER_KINDS:
                problems.append(f"Member {m.id} has unknown kind {m.kind!r}.")

        for s in self.supports:
            if s.node not in nid:
                problems.append(f"A support refers to missing node {s.node}.")
        for ld in self.nodal_loads:
            if ld.node not in nid:
                problems.append(f"A nodal load refers to missing node {ld.node}.")
        for ld in self.member_loads:
            if ld.member not in mid:
                problems.append(f"A member load refers to missing member {ld.member}.")
            if ld.frame not in ("local", "global"):
                problems.append(f"Member load on {ld.member} has frame {ld.frame!r}.")
        for ld in self.thermal_loads:
            if ld.member is not None and ld.member not in mid:
                problems.append(f"A thermal load refers to missing member {ld.member}.")

        if self.nodes and not any(any(s.fixed) or any(s.spring) for s in self.supports):
            problems.append("The model has no supports: it would float away.")
        return problems

    # ------------------------------------------------------------ persistence
    def to_dict(self) -> dict:
        return {
            "format_version": FORMAT_VERSION,
            "name": self.name,
            "dimension": self.dimension,
            "display_units": self.display_units,
            "self_weight": self.self_weight,
            "gravity": list(self.gravity),
            "notes": self.notes,
            "nodes": [n.to_dict() for n in self.nodes],
            "members": [m.to_dict() for m in self.members],
            "supports": [s.to_dict() for s in self.supports],
            "nodal_loads": [l.to_dict() for l in self.nodal_loads],
            "member_loads": [l.to_dict() for l in self.member_loads],
            "thermal_loads": [l.to_dict() for l in self.thermal_loads],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Model":
        version = d.get("format_version", 1)
        if version > FORMAT_VERSION:
            raise ValueError(
                f"File format version {version} is newer than this app supports ({FORMAT_VERSION})."
            )
        return cls(
            name=d.get("name", "Untitled"),
            dimension=int(d.get("dimension", 2)),
            nodes=[Node.from_dict(x) for x in d.get("nodes", [])],
            members=[Member.from_dict(x) for x in d.get("members", [])],
            supports=[Support.from_dict(x) for x in d.get("supports", [])],
            nodal_loads=[NodalLoad.from_dict(x) for x in d.get("nodal_loads", [])],
            member_loads=[MemberLoad.from_dict(x) for x in d.get("member_loads", [])],
            thermal_loads=[ThermalLoad.from_dict(x) for x in d.get("thermal_loads", [])],
            self_weight=bool(d.get("self_weight", False)),
            gravity=tuple(d.get("gravity", (0.0, -9.81, 0.0))),
            display_units=d.get("display_units", "SI"),
            notes=d.get("notes", ""),
        )
