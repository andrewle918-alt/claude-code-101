"""Load definitions (plain data). All values SI: N, N*m, N/m, K."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class NodalLoad:
    """Point force and/or moment applied at a node, in GLOBAL axes."""

    node: int
    force: tuple[float, float, float] = (0.0, 0.0, 0.0)    # (Fx, Fy, Fz) in N
    moment: tuple[float, float, float] = (0.0, 0.0, 0.0)   # (Mx, My, Mz) in N*m

    @classmethod
    def from_magnitude_angle(cls, node: int, magnitude: float, angle_deg: float) -> "NodalLoad":
        """2D load given as magnitude and angle measured CCW from global +x."""
        a = math.radians(angle_deg)
        return cls(node, force=(magnitude * math.cos(a), magnitude * math.sin(a), 0.0))

    def to_dict(self) -> dict:
        return {"node": self.node, "force": list(self.force), "moment": list(self.moment)}

    @classmethod
    def from_dict(cls, d: dict) -> "NodalLoad":
        return cls(int(d["node"]), tuple(d.get("force", (0, 0, 0))), tuple(d.get("moment", (0, 0, 0))))


@dataclass
class MemberLoad:
    """Distributed load on a member, varying linearly from start (i) to end (j).

    ``w_start`` / ``w_end`` are (wx, wy, wz) intensities in N/m.  A uniform
    load simply has ``w_start == w_end``.  ``frame`` says whether the
    components are in the member's LOCAL axes (x along the member, y
    transverse) or in GLOBAL axes.
    """

    member: int
    w_start: tuple[float, float, float] = (0.0, 0.0, 0.0)
    w_end: tuple[float, float, float] = (0.0, 0.0, 0.0)
    frame: str = "local"

    @classmethod
    def uniform(cls, member: int, wy: float, wx: float = 0.0, wz: float = 0.0,
                frame: str = "local") -> "MemberLoad":
        w = (wx, wy, wz)
        return cls(member, w, w, frame)

    def to_dict(self) -> dict:
        return {"member": self.member, "w_start": list(self.w_start),
                "w_end": list(self.w_end), "frame": self.frame}

    @classmethod
    def from_dict(cls, d: dict) -> "MemberLoad":
        return cls(int(d["member"]), tuple(d["w_start"]), tuple(d["w_end"]), d.get("frame", "local"))


@dataclass
class ThermalLoad:
    """Uniform temperature change (K) on one member, or on all if ``member`` is None."""

    delta_t: float
    member: int | None = None

    def to_dict(self) -> dict:
        return {"delta_t": self.delta_t, "member": self.member}

    @classmethod
    def from_dict(cls, d: dict) -> "ThermalLoad":
        m = d.get("member")
        return cls(float(d["delta_t"]), None if m is None else int(m))
