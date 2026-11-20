"""Node: a point in space where members connect."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Node:
    """A joint. Coordinates are in metres (SI). 2D models keep ``z = 0``."""

    id: int
    x: float
    y: float
    z: float = 0.0

    @property
    def xyz(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def to_dict(self) -> dict:
        return {"id": self.id, "x": self.x, "y": self.y, "z": self.z}

    @classmethod
    def from_dict(cls, d: dict) -> "Node":
        return cls(id=int(d["id"]), x=float(d["x"]), y=float(d["y"]), z=float(d.get("z", 0.0)))
