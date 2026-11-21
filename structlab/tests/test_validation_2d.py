"""Validation of the 2D solver against textbook / hand-calculable results."""
import math

import numpy as np
import pytest

from structlab.core import MemberLoad, Model, NodalLoad, Support, ThermalLoad
from structlab.solver import AnalysisOptions, InstabilityError, ModelError, member_diagram, solve
from structlab.solver import diagnostics as dg
from structlab.templates import textbook as T


def sec(A, I=1e-8):
    return T._custom(A, I)


# ------------------------------------------------------------------ truss ---------
def test_triangle_truss_member_forces_and_reactions():
    model, exp = T.triangle_truss()
    r = solve(model)
    assert r.reaction(1)[1] == pytest.approx(exp["R_A"][1], rel=1e-9)
    assert r.reaction(2)[1] == pytest.approx(exp["R_B"][1], rel=1e-9)
    assert abs(r.reaction(1)[0]) < 1e-6
    for mid, F in exp["F"].items():
        assert r.members[mid].axial == pytest.approx(F, rel=1e-9)
    assert r.members[1].state == "tension" and r.members[2].state == "compression"
    assert r.displacement(3)[1] == pytest.approx(exp["uy_C"], rel=1e-9)   # unit-load method
    assert r.diagnostics.degree_indeterminacy == 0       # m + r - 2j = 3 + 3 - 6
    assert r.diagnostics.equilibrium_ok


def test_axial_bar_elongation():
    model, exp = T.axial_bar()
    r = solve(model)
    assert r.displacement(2)[0] == pytest.approx(exp["delta"], rel=1e-12)   # PL/(AE)
    assert r.members[1].elongation == pytest.approx(exp["delta"], rel=1e-12)
    assert r.members[1].axial == pytest.approx(exp["N"], rel=1e-12)
    assert r.members[1].axial_stress == pytest.approx(50_000 / 5e-4)


def test_rotated_truss_member_gives_same_force():
    """A 3-4-5 bar loaded along its own axis carries that load, whatever its orientation."""
    m = Model()
    a, b = m.add_node(0, 0), m.add_node(3, 4)
    m.add_member(a.id, b.id, section=sec(1e-3))
    m.add_support(Support.pin2d(a.id))
    # inclined roller at b: restrains motion perpendicular to the bar, free along it
    m.add_support(Support(b.id, fixed=(False, True, True, True, True, False),
                          angle_deg=math.degrees(math.atan2(4, 3))))
    m.add_nodal_load(NodalLoad(b.id, force=(3000.0, 4000.0, 0.0)))   # 5 kN along the bar
    r = solve(m)
    assert r.members[1].axial == pytest.approx(5000.0, rel=1e-9)
    assert r.members[1].elongation == pytest.approx(5000 * 5 / (1e-3 * 200e9), rel=1e-9)


# ------------------------------------------------------------------ beams ---------
@pytest.mark.parametrize("n", [1, 4])
def test_cantilever_tip_load(n):
    model, e = T.cantilever_beam(n)
    r = solve(model)
    ux, uy, rz = r.displacement(e["tip_node"])
    assert uy == pytest.approx(e["tip_deflection"], rel=1e-9)     # -P L^3/(3 E I)
    assert rz == pytest.approx(e["tip_rotation"], rel=1e-9)       # -P L^2/(2 E I)
    Rx, Ry, Mz = r.reaction(e["root_node"])
    assert Ry == pytest.approx(e["V"], rel=1e-9)
    assert Mz == pytest.approx(e["M_fixed"], rel=1e-9)            # P L
    first = r.members[1]
    assert first.V_i == pytest.approx(e["V"], rel=1e-9)
    assert first.M_i == pytest.approx(-e["M_fixed"], rel=1e-9)    # hogging = negative
    assert r.diagnostics.degree_indeterminacy == 0


@pytest.mark.parametrize("n", [1, 2, 4])
def test_simply_supported_udl(n):
    model, e = T.simply_supported_beam(n)
    r = solve(model)
    assert r.reaction(1)[1] == pytest.approx(e["R"], rel=1e-9)
    # sample every member, find the global extremes
    Ms, vs = [], []
    for mem in r.members.values():
        d = member_diagram(mem, 201)
        Ms.append(d.M.max())
        vs.append(d.v.min())
    # midspan lies at a node when n is even, inside an element when n = 1: both are exact
    assert max(Ms) == pytest.approx(e["M_max"], rel=1e-6)          # w L^2 / 8
    assert min(vs) == pytest.approx(e["delta_max"], rel=1e-4)      # 5 w L^4 / (384 E I)
    assert r.displacement(1)[2] == pytest.approx(e["end_rotation"], rel=1e-9)   # -w L^3/(24 E I)


def test_diagram_matches_end_displacements():
    """Exact integration inside the member must land on the solved end-j displacement."""
    model, _ = T.simply_supported_beam(1)
    r = solve(model)
    mem = r.members[1]
    d = member_diagram(mem, 11)
    assert d.v[-1] == pytest.approx(mem.u_local[4], abs=1e-12)
    assert d.theta[-1] == pytest.approx(mem.u_local[5], rel=1e-9)
    assert d.M[-1] == pytest.approx(mem.M_j, abs=1e-6)
    assert d.V[-1] == pytest.approx(mem.V_j, abs=1e-6)


def test_propped_cantilever_indeterminate():
    model, e = T.propped_cantilever(2)
    r = solve(model)
    assert r.diagnostics.degree_indeterminacy == 1          # 3 members*... 2 frame members (6) + 4 restraints - 9 equations = 1
    assert r.reaction(e["prop_node"])[1] == pytest.approx(e["R_prop"], rel=1e-9)     # 3wL/8
    assert r.reaction(e["fixed_node"])[1] == pytest.approx(e["R_fixed"], rel=1e-9)   # 5wL/8
    assert r.reaction(e["fixed_node"])[2] == pytest.approx(e["M_fixed"], rel=1e-9)   # wL^2/8


def test_linearly_varying_load_equilibrium_and_reaction():
    """Triangular load 0 -> w on a simple beam: R_left = wL/6, R_right = wL/3."""
    L, w = 6.0, 9000.0
    m = Model()
    a, b = m.add_node(0, 0), m.add_node(L, 0)
    mem = m.add_member(a.id, b.id, kind="frame", section=sec(1e-2, 8e-5))
    m.add_member_load(MemberLoad(mem.id, (0, 0, 0), (0, -w, 0), frame="local"))
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support.roller2d(b.id))
    r = solve(m)
    assert r.reaction(a.id)[1] == pytest.approx(w * L / 6, rel=1e-9)
    assert r.reaction(b.id)[1] == pytest.approx(w * L / 3, rel=1e-9)
    assert r.diagnostics.equilibrium_ok


def test_inclined_member_load_uses_local_axes():
    """A global vertical UDL on an inclined beam: total vertical reaction equals the total load."""
    m = Model()
    a, b = m.add_node(0, 0), m.add_node(4, 3)
    mem = m.add_member(a.id, b.id, kind="frame", section=sec(1e-2, 8e-5))
    m.add_member_load(MemberLoad.uniform(mem.id, wy=-1000.0, frame="global"))
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support.roller2d(b.id))
    r = solve(m)
    assert r.total_reaction()[1] == pytest.approx(1000.0 * 5.0, rel=1e-9)   # w * L (L = 5 m)
    assert r.diagnostics.equilibrium_ok


# ------------------------------------------------------- supports and loads ----------
def test_spring_support():
    """Bar (k = EA/L) in series with a ground spring ks: u = P/(k + ks); spring force = ks u."""
    m = Model()
    a, b = m.add_node(0, 0), m.add_node(2, 0)
    m.add_member(a.id, b.id, section=sec(5e-4))
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support(b.id, fixed=(False, True, True, True, True, False),
                          spring=(1e7, 0, 0, 0, 0, 0)))
    m.add_nodal_load(NodalLoad(b.id, force=(10_000.0, 0, 0)))
    r = solve(m)
    k_bar = 5e-4 * 200e9 / 2.0
    u = 10_000.0 / (k_bar + 1e7)
    assert r.displacement(b.id)[0] == pytest.approx(u, rel=1e-9)
    assert r.reaction(b.id)[0] == pytest.approx(-1e7 * u, rel=1e-9)     # spring pulls back
    assert r.diagnostics.equilibrium_ok


def test_support_settlement():
    """Settlement of one end of a restrained bar: N = EA d / L (tension for an outward move)."""
    m = Model()
    a, b = m.add_node(0, 0), m.add_node(2, 0)
    m.add_member(a.id, b.id, section=sec(5e-4))
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support(b.id, fixed=(True, True, True, True, True, False),
                          settlement=(0.001, 0, 0, 0, 0, 0)))
    r = solve(m)
    assert r.members[1].axial == pytest.approx(5e-4 * 200e9 * 0.001 / 2.0, rel=1e-9)
    assert r.diagnostics.equilibrium_ok


def test_inclined_roller_reaction_is_normal_to_incline():
    m = Model()
    a, b = m.add_node(0, 0), m.add_node(4, 0)
    m.add_member(a.id, b.id, kind="frame", section=sec(1e-2, 8e-5))
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support.roller2d(b.id, angle_deg=30.0))   # incline normal rotated 30 deg
    m.add_nodal_load(NodalLoad(a.id, force=(0, -1000.0, 0)))
    m.add_nodal_load(NodalLoad(b.id, force=(0, -2000.0, 0)))
    r = solve(m)
    rx, ry, _ = r.reaction(b.id)
    th = math.radians(30)
    # reaction must be parallel to the rotated y axis (-sin th, cos th)
    assert rx * math.cos(th) + ry * math.sin(th) == pytest.approx(0.0, abs=1e-6)
    assert r.diagnostics.equilibrium_ok


def test_thermal_restrained_bar():
    """Fully restrained bar: N = -E A alpha dT (compression); free bar: delta = alpha dT L, N = 0."""
    E, A, alpha, dT, L = 200e9, 5e-4, 11.7e-6, 40.0, 2.0
    for restrained in (True, False):
        m = Model()
        a, b = m.add_node(0, 0), m.add_node(L, 0)
        m.add_member(a.id, b.id, section=sec(A))
        m.add_support(Support.pin2d(a.id))
        m.add_support(Support.pin2d(b.id) if restrained else Support.roller2d(b.id))
        m.thermal_loads.append(ThermalLoad(dT))
        r = solve(m)
        if restrained:
            assert r.members[1].axial == pytest.approx(-E * A * alpha * dT, rel=1e-9)
            assert r.members[1].state == "compression"
        else:
            assert r.members[1].axial == pytest.approx(0.0, abs=1e-6)
            assert r.displacement(b.id)[0] == pytest.approx(alpha * dT * L, rel=1e-9)
        assert r.diagnostics.equilibrium_ok


def test_self_weight_hanging_bar():
    """Hanging bar: support reaction = W = rho A g L; tip displacement = W L/(2 A E)."""
    m = Model(self_weight=True)
    a, b = m.add_node(0, 0), m.add_node(0, -3.0)
    m.add_member(a.id, b.id, section=sec(5e-4))        # A36: rho = 7850
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support(b.id, fixed=(True, False, True, True, True, False)))  # restrain x only
    r = solve(m)
    W = 7850 * 5e-4 * 3.0 * 9.81
    assert r.reaction(a.id)[1] == pytest.approx(W, rel=1e-9)
    assert r.displacement(b.id)[1] == pytest.approx(-W * 3.0 / (2 * 5e-4 * 200e9), rel=1e-9)


def test_load_factor_scales_linearly():
    model, _ = T.triangle_truss()
    r1 = solve(model)
    r2 = solve(model, AnalysisOptions(load_factor=2.5))
    assert r2.members[2].axial == pytest.approx(2.5 * r1.members[2].axial, rel=1e-12)
    assert r2.max_displacement == pytest.approx(2.5 * r1.max_displacement, rel=1e-12)


# ------------------------------------------------- failure reporting ---------------
def test_mechanism_is_reported_not_solved():
    """Square truss without a diagonal collapses (mechanism)."""
    m = Model()
    n = [m.add_node(0, 0), m.add_node(2, 0), m.add_node(2, 2), m.add_node(0, 2)]
    for i, j in [(0, 1), (1, 2), (2, 3), (3, 0)]:
        m.add_member(n[i].id, n[j].id, section=sec(1e-3))
    m.add_support(Support.pin2d(n[0].id))
    m.add_support(Support.roller2d(n[1].id))
    m.add_nodal_load(NodalLoad(n[2].id, force=(1000, 0, 0)))
    with pytest.raises(InstabilityError, match="unstable") as exc:
        solve(m)
    assert "diagonal" in str(exc.value)
    assert exc.value.diagnostics.degree_indeterminacy == -1     # m + r - 2j = 4 + 3 - 8


def test_adding_diagonal_makes_it_stable_and_determinate():
    m = Model()
    n = [m.add_node(0, 0), m.add_node(2, 0), m.add_node(2, 2), m.add_node(0, 2)]
    for i, j in [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]:
        m.add_member(n[i].id, n[j].id, section=sec(1e-3))
    m.add_support(Support.pin2d(n[0].id))
    m.add_support(Support.roller2d(n[1].id))
    m.add_nodal_load(NodalLoad(n[2].id, force=(1000, 0, 0)))
    r = solve(m)
    assert r.diagnostics.degree_indeterminacy == 0
    assert r.members[5].axial == pytest.approx(1000 * math.sqrt(2), rel=1e-9)   # diagonal carries H/cos45


def test_insufficient_supports():
    model, _ = T.triangle_truss()
    model.supports = [Support.pin2d(1)]           # only 2 restraints: rigid-body rotation possible
    with pytest.raises(InstabilityError, match="at least 3"):
        solve(model)


def test_no_supports_and_bad_data():
    model, _ = T.triangle_truss()
    model.supports = []
    with pytest.raises(ModelError, match="no supports"):
        solve(model)
    model, _ = T.triangle_truss()
    model.members[0].section = None
    with pytest.raises(ModelError, match="no cross-section"):
        solve(model)


def test_moment_at_pin_joint_rejected():
    model, _ = T.triangle_truss()
    model.add_nodal_load(NodalLoad(3, moment=(0, 0, 100.0)))
    with pytest.raises(ModelError, match="pin"):
        solve(model)


# ------------------------------------------------- equilibrium check itself ---------
def test_equilibrium_check_detects_wrong_reactions():
    applied = (0.0, -10_000.0, 0.0)
    good = [(0.0, 0.0, 0.0, 5000.0, 0.0), (6.0, 0.0, 0.0, 5000.0, 0.0)]
    # applied load sits at x = 3: moment about origin = 3 * (-10000)
    applied = (0.0, -10_000.0, 3.0 * -10_000.0)
    assert dg.check_equilibrium(applied, good)[0]
    bad = [(0.0, 0.0, 0.0, 5000.0, 0.0), (6.0, 0.0, 0.0, 4000.0, 0.0)]
    assert not dg.check_equilibrium(applied, bad)[0]


def test_equilibrium_failure_produces_visible_warning(monkeypatch):
    from structlab.solver import api
    monkeypatch.setattr(api.diagnostics, "check_equilibrium",
                        lambda a, r: (False, (1.0, 2.0, 3.0), (1e-6, 1e-6, 1e-6)))
    model, _ = T.triangle_truss()
    r = solve(model)
    assert not r.diagnostics.equilibrium_ok
    assert any("EQUILIBRIUM" in w for w in r.diagnostics.warnings)
    assert "FAILED" in r.summary()


def test_large_displacement_warning():
    m = Model()
    a, b = m.add_node(0, 0), m.add_node(1, 0)
    m.add_member(a.id, b.id, section=sec(1e-6))
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support.roller2d(b.id))
    m.add_nodal_load(NodalLoad(b.id, force=(1e6, 0, 0)))     # absurdly large stretch
    r = solve(m)
    assert any("small-displacement" in w for w in r.diagnostics.warnings)


def test_yield_flag_and_fos():
    m = Model()
    a, b = m.add_node(0, 0), m.add_node(2, 0)
    m.add_member(a.id, b.id, section=sec(1e-4))              # A36, Sy = 250 MPa
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support.roller2d(b.id))
    m.add_nodal_load(NodalLoad(b.id, force=(50_000.0, 0, 0)))    # 500 MPa
    r = solve(m)
    assert r.members[1].status == "yields"
    assert r.members[1].fos == pytest.approx(0.5)


def test_sparse_path_matches_dense(monkeypatch):
    """Force the large-model (sparse) branch on a small model and compare."""
    model, e = T.simply_supported_beam(8)
    dense = solve(model)
    from structlab.solver import diagnostics
    monkeypatch.setattr(diagnostics, "DENSE_LIMIT", 5)
    sparse = solve(model)
    assert sparse.max_displacement == pytest.approx(dense.max_displacement, rel=1e-9)
