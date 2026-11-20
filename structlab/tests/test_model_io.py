import json

import pytest

from structlab.core import Member, MemberLoad, Model, NodalLoad, Support, ThermalLoad
from structlab.io import load_model, save_model


def make_triangle() -> Model:
    m = Model(name="triangle", dimension=2)
    a = m.add_node(0, 0)
    b = m.add_node(4, 0)
    c = m.add_node(2, 3)
    for i, j in [(a.id, b.id), (b.id, c.id), (c.id, a.id)]:
        m.add_member(i, j, section={"kind": "round_bar", "params": {"d": 0.02}})
    m.add_support(Support.pin2d(a.id))
    m.add_support(Support.roller2d(b.id))
    m.add_nodal_load(NodalLoad(c.id, force=(0, -10000, 0)))
    m.add_member_load(MemberLoad.uniform(1, wy=-500))
    m.thermal_loads.append(ThermalLoad(25.0))
    return m


def test_valid_model_has_no_problems():
    assert make_triangle().validate() == []


def test_json_round_trip(tmp_path):
    model = make_triangle()
    path = tmp_path / "t.json"
    save_model(model, path)
    loaded = load_model(path)
    assert loaded.to_dict() == model.to_dict()
    # file is human readable JSON
    data = json.loads(path.read_text())
    assert data["format_version"] == 1 and len(data["nodes"]) == 3


def test_newer_format_rejected():
    with pytest.raises(ValueError):
        Model.from_dict({"format_version": 999})


def test_validation_catches_problems():
    m = Model()
    a = m.add_node(0, 0)
    m.add_node(0, 0)
    m.add_member(1, 2)                 # coincident nodes
    m.add_member(1, 99)                # missing node
    m.add_nodal_load(NodalLoad(42))    # missing node
    problems = " ".join(m.validate())
    assert "zero length" in problems
    assert "missing node" in problems
    assert "no supports" in problems


def test_inclined_load_helper():
    ld = NodalLoad.from_magnitude_angle(1, 100.0, 90.0)
    assert ld.force[0] == pytest.approx(0.0, abs=1e-12)
    assert ld.force[1] == pytest.approx(100.0)


def test_support_constructors():
    assert Support.pin2d(1).fixed[:2] == (True, True) and Support.pin2d(1).fixed[5] is False
    assert Support.roller2d(1).fixed[:2] == (False, True)
    assert all(Support.fixed3d(1).fixed)
    assert Support.roller3d(1, free="x").fixed[:3] == (False, True, True)
    with pytest.raises(ValueError):
        Support(1, fixed=(True, True))
