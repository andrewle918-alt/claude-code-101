"""Cross-section library: compute A, I, J from dimensions (all SI, metres).

Axis convention (matches the member LOCAL axes; x runs along the member):
    y  - in the plane of bending for 2D models (the "depth" direction)
    z  - the other transverse axis
    Iz = integral of y^2 dA   (strong-axis bending for a 2D beam; sigma = M*c_y/Iz)
    Iy = integral of z^2 dA   (bending about y, only used in 3D)
    J  = torsion constant
    c_y, c_z = largest distance from centroid to the extreme fibre in y / z

Unsymmetric sections (angle, channel about its weak axis) have a product of
inertia that is IGNORED here; bending is assumed to act about the centroidal
axes parallel to the sections' legs.  This is a stated simplification.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

INCH = 0.0254


@dataclass
class Section:
    """Computed section properties plus the spec that produced them."""

    kind: str
    params: dict
    A: float          # area, m^2
    Iz: float         # m^4
    Iy: float         # m^4
    J: float          # torsion constant, m^4
    c_y: float = float("nan")   # m
    c_z: float = float("nan")   # m

    @property
    def Sz(self) -> float:
        """Elastic section modulus for bending about z: Iz / c_y."""
        return self.Iz / self.c_y

    @property
    def Sy(self) -> float:
        """Elastic section modulus for bending about y: Iy / c_z."""
        return self.Iy / self.c_z

    def radius_of_gyration(self) -> float:
        """Smallest radius of gyration sqrt(I_min / A) (governs buckling)."""
        return math.sqrt(min(self.Iz, self.Iy) / self.A)

    def to_spec(self) -> dict:
        return {"kind": self.kind, "params": dict(self.params)}


# --------------------------------------------------------------------------- helpers
def _positive(**dims: float) -> None:
    for name, v in dims.items():
        if not v > 0:
            raise ValueError(f"Section dimension {name} must be > 0 (got {v}).")


def _composite(rects: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float, float, float]:
    """Properties of a shape built from rectangles.

    Each rectangle is (z_extent, y_extent, z_center, y_center) measured from any
    common origin.  Returns (A, Iz, Iy, c_y, c_z, y_centroid) about the centroid,
    using the parallel-axis theorem  I = I_own + A d^2  (any mechanics of
    materials text, "moments of inertia of composite areas").
    """
    A = sum(w * h for w, h, _, _ in rects)
    zc = sum(w * h * z for w, h, z, _ in rects) / A       # centroid  = sum(A_i z_i)/sum(A_i)
    yc = sum(w * h * y for w, h, _, y in rects) / A
    Iz = sum(w * h**3 / 12 + w * h * (y - yc) ** 2 for w, h, _, y in rects)
    Iy = sum(h * w**3 / 12 + w * h * (z - zc) ** 2 for w, h, z, _ in rects)
    y_top = max(y + h / 2 for _, h, _, y in rects) - yc
    y_bot = yc - min(y - h / 2 for _, h, _, y in rects)
    z_top = max(z + w / 2 for w, _, z, _ in rects) - zc
    z_bot = zc - min(z - w / 2 for w, _, z, _ in rects)
    return A, Iz, Iy, max(y_top, y_bot), max(z_top, z_bot), yc


# --------------------------------------------------------------------------- shapes
def round_bar(d: float) -> Section:
    """Solid circle. A = pi d^2/4, I = pi d^4/64, J = pi d^4/32."""
    _positive(d=d)
    return Section("round_bar", {"d": d}, math.pi * d**2 / 4, math.pi * d**4 / 64,
                   math.pi * d**4 / 64, math.pi * d**4 / 32, d / 2, d / 2)


def round_tube(do: float, t: float) -> Section:
    """Hollow circle: outer diameter ``do``, wall ``t``. J = pi (do^4 - di^4)/32."""
    _positive(do=do, t=t)
    if t >= do / 2:
        raise ValueError("Tube wall t must be less than half the outer diameter.")
    di = do - 2 * t
    I = math.pi * (do**4 - di**4) / 64
    return Section("round_tube", {"do": do, "t": t}, math.pi * (do**2 - di**2) / 4,
                   I, I, 2 * I, do / 2, do / 2)


def rect_bar(b: float, h: float) -> Section:
    """Solid rectangle. ``h`` = depth along y (in-plane bending), ``b`` = width along z.

    Iz = b h^3/12.  Torsion constant uses the common approximation (Shigley /
    Roark) with a >= b the long/short sides:
        J = a b^3 [1/3 - 0.21 (b/a) (1 - b^4 / (12 a^4))]
    """
    _positive(b=b, h=h)
    a, s = max(b, h), min(b, h)
    J = a * s**3 * (1 / 3 - 0.21 * (s / a) * (1 - s**4 / (12 * a**4)))
    return Section("rect_bar", {"b": b, "h": h}, b * h, b * h**3 / 12, h * b**3 / 12,
                   J, h / 2, b / 2)


def rect_tube(b: float, h: float, t: float) -> Section:
    """Hollow rectangle with uniform wall t. Closed thin-wall torsion (Bredt):
    J = 4 Am^2 t / perimeter_mid, using the mid-line dimensions."""
    _positive(b=b, h=h, t=t)
    if t >= min(b, h) / 2:
        raise ValueError("Tube wall t must be less than half of the smaller dimension.")
    bi, hi = b - 2 * t, h - 2 * t
    Am = (b - t) * (h - t)
    perim = 2 * ((b - t) + (h - t))
    return Section("rect_tube", {"b": b, "h": h, "t": t}, b * h - bi * hi,
                   (b * h**3 - bi * hi**3) / 12, (h * b**3 - hi * bi**3) / 12,
                   4 * Am**2 * t / perim, h / 2, b / 2)


def i_beam(d: float, bf: float, tf: float, tw: float) -> Section:
    """Doubly-symmetric I-shape (fillets neglected). Open thin-wall J = sum(b t^3)/3."""
    _positive(d=d, bf=bf, tf=tf, tw=tw)
    if 2 * tf >= d:
        raise ValueError("Flanges are thicker than the section depth allows (2*tf >= d).")
    hw = d - 2 * tf
    rects = [(bf, tf, bf / 2, tf / 2), (tw, hw, bf / 2, d / 2), (bf, tf, bf / 2, d - tf / 2)]
    A, Iz, Iy, cy, cz, _ = _composite(rects)
    J = (2 * bf * tf**3 + hw * tw**3) / 3
    return Section("i_beam", {"d": d, "bf": bf, "tf": tf, "tw": tw}, A, Iz, Iy, J, cy, cz)


def channel(d: float, bf: float, tf: float, tw: float) -> Section:
    """C-channel: web depth ``d`` along y, flanges ``bf`` wide (fillets neglected).
    Centroid is offset from the web, so Iy is taken about the true centroid."""
    _positive(d=d, bf=bf, tf=tf, tw=tw)
    if 2 * tf >= d or tw >= bf:
        raise ValueError("Channel thicknesses are too large for its overall dimensions.")
    fw = bf - tw   # flange length beyond the web
    rects = [(tw, d, tw / 2, d / 2),
             (fw, tf, tw + fw / 2, tf / 2),
             (fw, tf, tw + fw / 2, d - tf / 2)]
    A, Iz, Iy, cy, cz, _ = _composite(rects)
    J = (2 * bf * tf**3 + (d - 2 * tf) * tw**3) / 3
    return Section("channel", {"d": d, "bf": bf, "tf": tf, "tw": tw}, A, Iz, Iy, J, cy, cz)


def angle(b: float, h: float, t: float) -> Section:
    """L-angle: vertical leg ``h`` (along y), horizontal leg ``b`` (along z), thickness t.
    Properties are about the centroidal axes parallel to the legs (product of inertia ignored)."""
    _positive(b=b, h=h, t=t)
    if t >= min(b, h):
        raise ValueError("Angle thickness must be less than both leg lengths.")
    rects = [(t, h, t / 2, h / 2), (b - t, t, t + (b - t) / 2, t / 2)]
    A, Iz, Iy, cy, cz, _ = _composite(rects)
    J = (h + b - t) * t**3 / 3
    return Section("angle", {"b": b, "h": h, "t": t}, A, Iz, Iy, J, cy, cz)


def w_shape(name: str) -> Section:
    """A named AISC W-shape from ``wshapes.json`` (nominal dims, fillets neglected)."""
    shapes = _wshape_table()
    if name not in shapes:
        raise KeyError(f"Unknown W-shape {name!r}. Available: {sorted(shapes)}")
    s = shapes[name]
    sec = i_beam(s["d"] * INCH, s["bf"] * INCH, s["tf"] * INCH, s["tw"] * INCH)
    sec.kind, sec.params = "w_shape", {"name": name}
    return sec


def custom(A: float, Iz: float, Iy: float, J: float,
           c_y: float = float("nan"), c_z: float = float("nan")) -> Section:
    """User-entered properties. ``c_y``/``c_z`` are needed for bending stress."""
    _positive(A=A, Iz=Iz, Iy=Iy, J=J)
    params = {"A": A, "Iz": Iz, "Iy": Iy, "J": J}
    if not math.isnan(c_y):
        params["c_y"] = c_y
    if not math.isnan(c_z):
        params["c_z"] = c_z
    return Section("custom", params, A, Iz, Iy, J, c_y, c_z)


_WSHAPES: dict | None = None


def _wshape_table() -> dict:
    global _WSHAPES
    if _WSHAPES is None:
        path = Path(__file__).with_name("wshapes.json")
        _WSHAPES = json.loads(path.read_text(encoding="utf-8"))["shapes"]
    return _WSHAPES


def w_shape_names() -> list[str]:
    return sorted(_wshape_table())


SECTION_FACTORIES: dict[str, Callable[..., Section]] = {
    "round_bar": round_bar, "round_tube": round_tube, "rect_bar": rect_bar,
    "rect_tube": rect_tube, "i_beam": i_beam, "channel": channel, "angle": angle,
    "w_shape": w_shape, "custom": custom,
}


def make_section(kind: str, **params: float) -> Section:
    """Build a Section from a spec, e.g. ``make_section('round_bar', d=0.02)``."""
    try:
        factory = SECTION_FACTORIES[kind]
    except KeyError:
        raise KeyError(f"Unknown section kind {kind!r}. Available: {sorted(SECTION_FACTORIES)}") from None
    return factory(**params)


def section_from_spec(spec: dict) -> Section:
    """Inverse of ``Section.to_spec()`` (used when loading a Member's section)."""
    return make_section(spec["kind"], **spec.get("params", {}))
