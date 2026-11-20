"""Supports: restraints, inclined rollers, settlements and springs at a node.

DOF order everywhere in StructLab: (ux, uy, uz, rx, ry, rz).
2D models only use ux, uy and rz.
"""
from __future__ import annotations

from dataclasses import dataclass, field

DOF_NAMES = ("ux", "uy", "uz", "rx", "ry", "rz")


def _six(values, default) -> tuple:
    vals = tuple(values) if values is not None else (default,) * 6
    if len(vals) != 6:
        raise ValueError("expected 6 values in (ux, uy, uz, rx, ry, rz) order")
    return vals


@dataclass
class Support:
    """Restraint data for one node.

    fixed       -- True where the DOF is restrained.
    angle_deg   -- 2D inclined roller: rotate the restrained direction by this
                   angle (0 = restrained along global x/y as flagged).
    settlement  -- prescribed displacement for restrained DOFs (m or rad).
    spring      -- elastic support stiffness per DOF (N/m or N*m/rad); 0 = none.
    """

    node: int
    fixed: tuple[bool, ...] = (False,) * 6
    angle_deg: float = 0.0
    settlement: tuple[float, ...] = (0.0,) * 6
    spring: tuple[float, ...] = (0.0,) * 6

    def __post_init__(self) -> None:
        self.fixed = tuple(bool(v) for v in _six(self.fixed, False))
        self.settlement = tuple(float(v) for v in _six(self.settlement, 0.0))
        self.spring = tuple(float(v) for v in _six(self.spring, 0.0))

    # ---- convenient constructors (2D) ----
    @classmethod
    def pin2d(cls, node: int) -> "Support":
        """2D pin: ux, uy restrained, rotation free."""
        return cls(node, fixed=(True, True, True, True, True, False))

    @classmethod
    def roller2d(cls, node: int, direction: str = "y", angle_deg: float = 0.0) -> "Support":
        """2D roller restraining motion along ``direction`` ('y' = vertical reaction)."""
        fx = direction == "x"
        return cls(node, fixed=(fx, not fx, True, True, True, False), angle_deg=angle_deg)

    @classmethod
    def fixed2d(cls, node: int) -> "Support":
        """2D fixed (clamped) support."""
        return cls(node, fixed=(True,) * 6)

    # ---- convenient constructors (3D) ----
    @classmethod
    def pin3d(cls, node: int) -> "Support":
        """3D ball-and-socket: all translations restrained, rotations free."""
        return cls(node, fixed=(True, True, True, False, False, False))

    @classmethod
    def roller3d(cls, node: int, free: str = "x") -> "Support":
        """3D roller: all translations restrained except along ``free`` axis."""
        flags = {"x": 0, "y": 1, "z": 2}[free]
        fixed = [True, True, True, False, False, False]
        fixed[flags] = False
        return cls(node, fixed=tuple(fixed))

    @classmethod
    def fixed3d(cls, node: int) -> "Support":
        return cls(node, fixed=(True,) * 6)

    def to_dict(self) -> dict:
        return {
            "node": self.node, "fixed": list(self.fixed), "angle_deg": self.angle_deg,
            "settlement": list(self.settlement), "spring": list(self.spring),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Support":
        return cls(
            node=int(d["node"]), fixed=tuple(d.get("fixed", (False,) * 6)),
            angle_deg=float(d.get("angle_deg", 0.0)),
            settlement=tuple(d.get("settlement", (0.0,) * 6)),
            spring=tuple(d.get("spring", (0.0,) * 6)),
        )
