"""Material data class and the editable material library (loaded from JSON)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_LIBRARY_PATH = Path(__file__).with_name("materials.json")


@dataclass
class Material:
    """Linear-elastic material, all properties in base SI (Pa, kg/m^3, 1/K).

    NOTE: values are *typical*, not design-certified.
    """

    name: str
    E: float                     # Young's modulus, Pa
    G: float                     # shear modulus, Pa
    nu: float                    # Poisson's ratio
    density: float               # kg/m^3
    yield_strength: float        # Pa (tension; brittle materials: tensile ultimate)
    ultimate_strength: float     # Pa
    cte: float                   # coefficient of thermal expansion, 1/K
    compressive_strength: float | None = None   # Pa, if different from tensile
    fatigue_strength: float | None = None       # Pa, completely reversed at fatigue_cycles
    fatigue_cycles: float | None = None
    has_endurance_limit: bool = False
    brittle: bool = False
    compression_only: bool = False
    orthotropic: bool = False
    warning: str = ""
    notes: str = ""
    source: str = ""

    # ----- JSON (friendly units: GPa, MPa, 1e-6/K) -----
    def to_json_dict(self) -> dict:
        d = {
            "name": self.name,
            "E_GPa": self.E / 1e9, "G_GPa": self.G / 1e9, "nu": self.nu,
            "density": self.density,
            "yield_MPa": self.yield_strength / 1e6,
            "ultimate_MPa": self.ultimate_strength / 1e6,
            "cte_1e6": self.cte * 1e6,
            "has_endurance_limit": self.has_endurance_limit,
        }
        if self.compressive_strength is not None:
            d["compressive_MPa"] = self.compressive_strength / 1e6
        if self.fatigue_strength is not None:
            d["fatigue_strength_MPa"] = self.fatigue_strength / 1e6
            d["fatigue_cycles"] = self.fatigue_cycles
        for flag in ("brittle", "compression_only", "orthotropic"):
            if getattr(self, flag):
                d[flag] = True
        for text in ("warning", "notes", "source"):
            if getattr(self, text):
                d[text] = getattr(self, text)
        return d

    @classmethod
    def from_json_dict(cls, d: dict) -> "Material":
        def opt_mpa(key: str) -> float | None:
            return d[key] * 1e6 if key in d else None

        return cls(
            name=d["name"],
            E=d["E_GPa"] * 1e9, G=d["G_GPa"] * 1e9, nu=d["nu"], density=d["density"],
            yield_strength=d["yield_MPa"] * 1e6, ultimate_strength=d["ultimate_MPa"] * 1e6,
            cte=d["cte_1e6"] * 1e-6,
            compressive_strength=opt_mpa("compressive_MPa"),
            fatigue_strength=opt_mpa("fatigue_strength_MPa"),
            fatigue_cycles=d.get("fatigue_cycles"),
            has_endurance_limit=bool(d.get("has_endurance_limit", False)),
            brittle=bool(d.get("brittle", False)),
            compression_only=bool(d.get("compression_only", False)),
            orthotropic=bool(d.get("orthotropic", False)),
            warning=d.get("warning", ""), notes=d.get("notes", ""), source=d.get("source", ""),
        )


class MaterialLibrary:
    """A name -> Material collection that can be loaded, extended, and saved."""

    def __init__(self, materials: list[Material] | None = None) -> None:
        self._items: dict[str, Material] = {}
        for m in materials or []:
            self.add(m)

    @classmethod
    def load(cls, path: str | Path = DEFAULT_LIBRARY_PATH) -> "MaterialLibrary":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([Material.from_json_dict(d) for d in data["materials"]])

    def save(self, path: str | Path) -> None:
        payload = {"materials": [m.to_json_dict() for m in self._items.values()]}
        Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def add(self, material: Material) -> None:
        """Add or replace a material (matched by name)."""
        self._items[material.name] = material

    def get(self, name: str) -> Material:
        try:
            return self._items[name]
        except KeyError:
            raise KeyError(f"Unknown material {name!r}. Available: {self.names()}") from None

    def names(self) -> list[str]:
        return list(self._items)

    def __contains__(self, name: str) -> bool:
        return name in self._items

    def __len__(self) -> int:
        return len(self._items)


_default: MaterialLibrary | None = None


def default_library() -> MaterialLibrary:
    """The built-in library, loaded once and cached."""
    global _default
    if _default is None:
        _default = MaterialLibrary.load()
    return _default
