"""Textbook validation models with hand-calculable answers.

Each builder returns ``(model, expected)`` where ``expected`` holds the closed-form
results (SI units).  They are used by the pytest validation suite, by
``examples/build_examples.py`` (which writes them to JSON so you can open them in
the GUI later) and by ``examples/validation_report.py``.

Steel: A36, E = 200 GPa.
"""
from __future__ import annotations

from ..core import Model, MemberLoad, NodalLoad, Support

E_STEEL = 200e9


def _custom(A: float, I: float = 1e-8) -> dict:
    """Custom section spec: area A, second moment I (also used for Iy), tiny J."""
    return {"kind": "custom", "params": {"A": A, "Iz": I, "Iy": I, "J": 1e-8, "c_y": 0.05, "c_z": 0.05}}


def triangle_truss() -> tuple[Model, dict]:
    """Symmetric 3-4-5 triangular truss, 10 kN vertical load at the apex.

    Joints: A(0,0) pin, B(6,0) roller, C(3,4) apex.  Members: 1=AB, 2=BC, 3=CA.  A = 1e-3 m^2.
    Method of joints: R_A = R_B = 5 kN.  Joint C: 2 F sin(theta) = 10 kN with sin = 4/5
    -> F_BC = F_CA = -6.25 kN (compression).  Joint A: F_AB = 6.25 * 3/5 = +3.75 kN (tension).
    Apex deflection by unit-load method: sum(F f L)/(AE) = 47500/(2e8) = 2.375e-4 m (down).
    """
    m = Model(name="Triangle truss (3-4-5)",
              notes="Hand check: R_A=R_B=5 kN; F_AB=+3.75 kN (T); F_BC=F_CA=-6.25 kN (C); "
                    "apex uy = -2.375e-4 m.")
    a, b, c = m.add_node(0, 0), m.add_node(6, 0), m.add_node(3, 4)
    sec = _custom(1e-3)
    m.add_member(a.id, b.id, section=sec)
    m.add_member(b.id, c.id, section=sec)
    m.add_member(c.id, a.id, section=sec)
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support.roller2d(b.id))
    m.add_nodal_load(NodalLoad(c.id, force=(0.0, -10_000.0, 0.0)))
    exp = {"R_A": (0.0, 5000.0), "R_B": (0.0, 5000.0), "F": {1: 3750.0, 2: -6250.0, 3: -6250.0},
           "uy_C": -2.375e-4}
    return m, exp


def axial_bar() -> tuple[Model, dict]:
    """Bar of length 2 m, A = 5e-4 m^2, pulled by P = 50 kN:  delta = P L/(A E) = 1.0 mm, N = P."""
    m = Model(name="Axial bar", notes="delta = PL/(AE) = 1.0 mm; N = +50 kN.")
    a, b = m.add_node(0, 0), m.add_node(2, 0)
    m.add_member(a.id, b.id, section=_custom(5e-4))
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support.roller2d(b.id))          # restrains y only, so the bar may stretch in x
    m.add_nodal_load(NodalLoad(b.id, force=(50_000.0, 0.0, 0.0)))
    return m, {"delta": 50_000.0 * 2.0 / (5e-4 * E_STEEL), "N": 50_000.0}


def cantilever_beam(n_elements: int = 1) -> tuple[Model, dict]:
    """Cantilever, L = 3 m, EI = 1.6e7 N m^2, tip load P = 10 kN down.

    Tip deflection PL^3/(3EI) = 5.625 mm, tip rotation PL^2/(2EI) = 2.8125e-3 rad,
    fixed-end moment PL = 30 kN m, shear P = 10 kN.
    """
    L, P, I = 3.0, 10_000.0, 8e-5
    m = Model(name=f"Cantilever beam ({n_elements} element{'s' if n_elements > 1 else ''})",
              notes="Tip deflection PL^3/(3EI)=5.625 mm down; M_fixed=PL=30 kN*m; V=10 kN.")
    nodes = [m.add_node(L * k / n_elements, 0.0) for k in range(n_elements + 1)]
    for k in range(n_elements):
        m.add_member(nodes[k].id, nodes[k + 1].id, kind="frame", section=_custom(1e-2, I))
    m.add_support(Support.fixed2d(nodes[0].id))
    m.add_nodal_load(NodalLoad(nodes[-1].id, force=(0.0, -P, 0.0)))
    EI = E_STEEL * I
    return m, {"tip_deflection": -P * L**3 / (3 * EI), "tip_rotation": -P * L**2 / (2 * EI),
               "M_fixed": P * L, "V": P, "tip_node": nodes[-1].id, "root_node": nodes[0].id, "EI": EI}


def simply_supported_beam(n_elements: int = 1) -> tuple[Model, dict]:
    """Simply supported beam, L = 6 m, uniform load w = 5 kN/m downward, EI = 1.6e7 N m^2.

    M_max = wL^2/8 = 22.5 kN m (midspan);  delta_max = 5 w L^4/(384 EI) = 5.273 mm;
    reactions wL/2 = 15 kN;  end rotation wL^3/(24 EI) = 2.8125e-3 rad.
    """
    L, w, I = 6.0, 5_000.0, 8e-5
    m = Model(name=f"Simply supported beam, UDL ({n_elements} element{'s' if n_elements > 1 else ''})",
              notes="M_max=wL^2/8=22.5 kN*m; delta_max=5wL^4/(384EI)=5.273 mm; R=15 kN each.")
    nodes = [m.add_node(L * k / n_elements, 0.0) for k in range(n_elements + 1)]
    for k in range(n_elements):
        mem = m.add_member(nodes[k].id, nodes[k + 1].id, kind="frame", section=_custom(1e-2, I))
        m.add_member_load(MemberLoad.uniform(mem.id, wy=-w, frame="global"))
    m.add_support(Support.pin2d(nodes[0].id))
    m.add_support(Support.roller2d(nodes[-1].id))
    EI = E_STEEL * I
    return m, {"M_max": w * L**2 / 8, "delta_max": -5 * w * L**4 / (384 * EI), "R": w * L / 2,
               "end_rotation": -w * L**3 / (24 * EI), "L": L, "EI": EI,
               "left_node": nodes[0].id}


def propped_cantilever(n_elements: int = 2) -> tuple[Model, dict]:
    """Propped cantilever (fixed left, roller right), L = 6 m, w = 5 kN/m: statically indeterminate.

    Classic result (Beer & Johnston / any statics text): R_prop = 3wL/8 = 11.25 kN,
    R_fixed = 5wL/8 = 18.75 kN, M_fixed = wL^2/8 = 22.5 kN m (resisting).
    """
    L, w, I = 6.0, 5_000.0, 8e-5
    m = Model(name="Propped cantilever, UDL", notes="R_prop=3wL/8=11.25 kN; M_fixed=wL^2/8=22.5 kN*m.")
    nodes = [m.add_node(L * k / n_elements, 0.0) for k in range(n_elements + 1)]
    for k in range(n_elements):
        mem = m.add_member(nodes[k].id, nodes[k + 1].id, kind="frame", section=_custom(1e-2, I))
        m.add_member_load(MemberLoad.uniform(mem.id, wy=-w, frame="global"))
    m.add_support(Support.fixed2d(nodes[0].id))
    m.add_support(Support.roller2d(nodes[-1].id))
    return m, {"R_prop": 3 * w * L / 8, "R_fixed": 5 * w * L / 8, "M_fixed": w * L**2 / 8,
               "fixed_node": nodes[0].id, "prop_node": nodes[-1].id}


# name used for the JSON file -> builder
EXAMPLES = {
    "01_triangle_truss": triangle_truss,
    "02_axial_bar": axial_bar,
    "03_cantilever_beam": lambda: cantilever_beam(4),
    "04_simply_supported_beam_udl": lambda: simply_supported_beam(4),
    "05_propped_cantilever_udl": lambda: propped_cantilever(4),
}
