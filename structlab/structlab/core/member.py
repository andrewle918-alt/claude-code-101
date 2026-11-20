"""Member: a straight element joining two nodes."""
from __future__ import annotations

from dataclasses import dataclass, field

# Member kinds
TRUSS = "truss"   # pin-jointed bar, carries axial force only
FRAME = "frame"   # beam/frame element: axial + shear + bending (+ torsion in 3D)
LINK = "link"     # rigid link (used by the machine solver)
CABLE = "cable"   # carries tension only
MEMBER_KINDS = (TRUSS, FRAME, LINK, CABLE)


@dataclass
class Member:
    """A member between node ``i`` and node ``j`` (local x axis points i -> j).

    ``section`` is a *spec*, not computed properties:
    ``{"kind": "round_bar", "params": {"d": 0.02}}`` (all lengths in metres).
    Keeping a spec means the JSON file stays human-readable and editable.
    """

    id: int
    i: int
    j: int
    kind: str = TRUSS
    material: str = "A36 Steel"
    section: dict | None = None
    release_i: bool = False   # moment release (pin) at node i end  (frames only)
    release_j: bool = False   # moment release (pin) at node j end  (frames only)
    k_factor: float = 1.0     # effective-length factor K for buckling (Phase 5)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "i": self.i, "j": self.j, "kind": self.kind,
            "material": self.material, "section": self.section,
            "release_i": self.release_i, "release_j": self.release_j,
            "k_factor": self.k_factor,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Member":
        return cls(
            id=int(d["id"]), i=int(d["i"]), j=int(d["j"]),
            kind=d.get("kind", TRUSS), material=d.get("material", "A36 Steel"),
            section=d.get("section"),
            release_i=bool(d.get("release_i", False)),
            release_j=bool(d.get("release_j", False)),
            k_factor=float(d.get("k_factor", 1.0)),
        )
