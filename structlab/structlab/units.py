"""Unit handling for StructLab.

DESIGN RULE: everything inside the model and solver is in base SI
(m, N, N*m, Pa, kg, K, rad).  This is the ONLY module that converts to or from
display units (GUI fields, tables, reports).  Never sprinkle conversion
factors anywhere else.

Each display unit is described by ``factor`` = how many SI units one display
unit equals, so::

    si_value      = display_value * factor      (to_si)
    display_value = si_value / factor           (from_si)
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Unit:
    """A display unit: its label and its size in SI."""

    label: str
    factor: float  # SI value of ONE display unit


# --- exact definitions of the US customary base units -------------------------
INCH = 0.0254                      # m, exact by definition
LBF = 4.4482216152605              # N, exact (lbm * standard gravity)
PSI = LBF / INCH**2                # Pa  (1 lbf / in^2)
LB_PER_IN3 = 0.45359237 / INCH**3  # kg/m^3  (1 lbm / in^3)
DEG = math.pi / 180.0              # rad

SYSTEMS: dict[str, dict[str, Unit]] = {
    "SI": {
        "length": Unit("m", 1.0),
        "displacement": Unit("mm", 1e-3),
        "force": Unit("kN", 1e3),
        "moment": Unit("kN·m", 1e3),
        "dist_load": Unit("kN/m", 1e3),
        "stress": Unit("MPa", 1e6),
        "modulus": Unit("GPa", 1e9),
        "density": Unit("kg/m³", 1.0),
        "area": Unit("mm²", 1e-6),
        "inertia": Unit("mm⁴", 1e-12),
        "temperature": Unit("K", 1.0),        # temperature CHANGE (delta)
        "cte": Unit("1/K", 1.0),
        "angle": Unit("deg", DEG),
    },
    "US": {
        "length": Unit("in", INCH),
        "displacement": Unit("in", INCH),
        "force": Unit("lbf", LBF),
        "moment": Unit("lbf·in", LBF * INCH),
        "dist_load": Unit("lbf/in", LBF / INCH),
        "stress": Unit("psi", PSI),
        "modulus": Unit("Msi", 1e6 * PSI),
        "density": Unit("lb/in³", LB_PER_IN3),
        "area": Unit("in²", INCH**2),
        "inertia": Unit("in⁴", INCH**4),
        "temperature": Unit("°F", 5.0 / 9.0),  # a change of 1 °F = 5/9 K
        "cte": Unit("1/°F", 9.0 / 5.0),        # alpha per °F -> alpha per K: x 9/5
        "angle": Unit("deg", DEG),
    },
}


def _unit(quantity: str, system: str) -> Unit:
    try:
        return SYSTEMS[system][quantity]
    except KeyError as exc:
        raise KeyError(
            f"Unknown quantity/system: {quantity!r}/{system!r}. "
            f"Quantities: {sorted(SYSTEMS['SI'])}; systems: {sorted(SYSTEMS)}"
        ) from exc


def to_si(quantity: str, value: float, system: str = "SI") -> float:
    """Convert a display value (e.g. 12 ksi typed by the user) to base SI."""
    return value * _unit(quantity, system).factor


def from_si(quantity: str, value: float, system: str = "SI") -> float:
    """Convert a base-SI value to the display system."""
    return value / _unit(quantity, system).factor


def unit_label(quantity: str, system: str = "SI") -> str:
    """Label string for a quantity, e.g. ``unit_label('stress', 'US') == 'psi'``."""
    return _unit(quantity, system).label


def format_value(quantity: str, si_value: float, system: str = "SI", digits: int = 4) -> str:
    """Human-readable string such as ``'12.5 kN'`` from an SI value."""
    v = from_si(quantity, si_value, system)
    return f"{v:.{digits}g} {unit_label(quantity, system)}"
