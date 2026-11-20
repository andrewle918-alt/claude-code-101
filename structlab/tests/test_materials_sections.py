import math

import pytest

from structlab.materials import MaterialLibrary, default_library, make_section, section_from_spec
from structlab.materials import sections as S

REQUIRED = [
    "A36 Steel", "A992 Steel", "High-Strength Steel (A514)", "Stainless Steel 304",
    "Aluminum 6061-T6", "Aluminum 2024-T3", "Titanium Ti-6Al-4V", "Gray Cast Iron (Class 30)",
    "Brass (Yellow, C27000)", "Copper (C11000)", "Douglas Fir (along grain)",
    "Oak (Red, along grain)", "Carbon Fiber Composite (UD, fibre direction)",
    "Concrete (f'c = 30 MPa)",
]


def test_required_materials_present_and_sane():
    lib = default_library()
    for name in REQUIRED:
        m = lib.get(name)
        assert m.E > 0 and m.G > 0 and 0 < m.nu < 0.5 and m.density > 0
        assert m.yield_strength > 0 and m.ultimate_strength >= m.yield_strength
    assert lib.get("A36 Steel").E == pytest.approx(200e9)
    assert lib.get("Concrete (f'c = 30 MPa)").compression_only
    assert lib.get("Carbon Fiber Composite (UD, fibre direction)").warning
    # steel G consistent with E / (2(1+nu)) within a few percent
    st = lib.get("A36 Steel")
    assert st.G == pytest.approx(st.E / (2 * (1 + st.nu)), rel=0.03)


def test_library_save_load_roundtrip(tmp_path):
    lib = default_library()
    p = tmp_path / "lib.json"
    lib.save(p)
    again = MaterialLibrary.load(p)
    assert again.names() == lib.names()
    assert again.get("Aluminum 6061-T6").yield_strength == pytest.approx(276e6)


def test_unknown_material_message():
    with pytest.raises(KeyError, match="Available"):
        default_library().get("Unobtainium")


def test_round_bar_and_tube():
    d = 0.05
    s = S.round_bar(d)
    assert s.A == pytest.approx(math.pi * d**2 / 4)
    assert s.Iz == pytest.approx(math.pi * d**4 / 64)
    assert s.J == pytest.approx(2 * s.Iz)
    t = S.round_tube(0.05, 0.005)
    assert t.A == pytest.approx(math.pi / 4 * (0.05**2 - 0.04**2))
    assert t.Sz == pytest.approx(t.Iz / 0.025)


def test_rectangle():
    s = S.rect_bar(b=0.02, h=0.06)
    assert s.Iz == pytest.approx(0.02 * 0.06**3 / 12)
    assert s.Iy == pytest.approx(0.06 * 0.02**3 / 12)
    # square torsion constant ~0.1406 a^4
    assert S.rect_bar(0.1, 0.1).J == pytest.approx(0.1406 * 0.1**4, rel=0.01)


def test_rect_tube_matches_difference_of_rectangles():
    s = S.rect_tube(0.04, 0.08, 0.004)
    assert s.A == pytest.approx(0.04 * 0.08 - 0.032 * 0.072)
    assert s.Iz == pytest.approx((0.04 * 0.08**3 - 0.032 * 0.072**3) / 12)


def test_i_beam_closed_form():
    d, bf, tf, tw = 0.3, 0.15, 0.012, 0.008
    s = S.i_beam(d, bf, tf, tw)
    assert s.A == pytest.approx(2 * bf * tf + (d - 2 * tf) * tw)
    assert s.Iz == pytest.approx((bf * d**3 - (bf - tw) * (d - 2 * tf) ** 3) / 12)
    assert s.c_y == pytest.approx(d / 2)


def test_wshapes_close_to_aisc_tables():
    import json
    from pathlib import Path
    table = json.loads((Path(S.__file__).with_name("wshapes.json")).read_text())["shapes"]
    for name, ref in table.items():
        sec = S.w_shape(name)
        A_in2 = sec.A / S.INCH**2
        I_in4 = sec.Iz / S.INCH**4
        assert A_in2 == pytest.approx(ref["ref_A_in2"], rel=0.05), name
        assert I_in4 == pytest.approx(ref["ref_Ix_in4"], rel=0.05), name


def test_angle_centroid_known_case():
    # L4x4x1/2 style check: equal-leg angle centroid is at (b^2 + h t - t^2)/(2(b+h-t)) from the back
    b = h = 0.1
    t = 0.01
    s = S.angle(b, h, t)
    assert s.A == pytest.approx(2 * b * t - t**2)
    xbar = (b**2 + h * t - t**2) / (2 * (b + h - t))
    # equal legs: distance to far fibre = b - xbar
    assert s.c_y == pytest.approx(h - xbar)
    assert s.Iz == pytest.approx(s.Iy)       # symmetric about the 45 degree axis


def test_channel_centroid_offset():
    s = S.channel(0.2, 0.075, 0.011, 0.0075)
    assert s.Iz > s.Iy > 0
    assert s.c_z > 0.075 / 2          # far fibre is the flange tip (centroid sits near the web)


def test_custom_and_spec_round_trip():
    s = S.custom(A=1e-3, Iz=2e-6, Iy=1e-6, J=3e-6, c_y=0.05, c_z=0.04)
    assert s.Sz == pytest.approx(2e-6 / 0.05)
    spec = make_section("round_tube", do=0.05, t=0.004).to_spec()
    again = section_from_spec(spec)
    assert again.A == pytest.approx(make_section("round_tube", do=0.05, t=0.004).A)


def test_bad_dimensions_rejected():
    with pytest.raises(ValueError):
        S.round_bar(-1)
    with pytest.raises(ValueError):
        S.round_tube(0.02, 0.02)
    with pytest.raises(KeyError):
        make_section("triangle", a=1)
