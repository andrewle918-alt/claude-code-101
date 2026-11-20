import math

import pytest

from structlab import units


def test_si_round_trip():
    for q in units.SYSTEMS["SI"]:
        assert units.from_si(q, units.to_si(q, 12.34, "SI"), "SI") == pytest.approx(12.34)


def test_us_round_trip():
    for q in units.SYSTEMS["US"]:
        assert units.from_si(q, units.to_si(q, 12.34, "US"), "US") == pytest.approx(12.34)


def test_known_conversions():
    assert units.to_si("length", 1, "US") == pytest.approx(0.0254)
    assert units.to_si("force", 1, "US") == pytest.approx(4.4482216)
    assert units.to_si("stress", 1, "US") == pytest.approx(6894.757, rel=1e-6)
    # Steel E = 29 Msi is about 200 GPa
    assert units.to_si("modulus", 29, "US") == pytest.approx(200e9, rel=0.01)
    assert units.to_si("force", 1, "SI") == 1000.0           # 1 kN
    assert units.to_si("angle", 180, "SI") == pytest.approx(math.pi)
    # A temperature CHANGE of 9 F is 5 K; alpha of 1/F is 1.8/K
    assert units.to_si("temperature", 9, "US") == pytest.approx(5.0)
    assert units.to_si("cte", 6.5e-6, "US") == pytest.approx(11.7e-6)


def test_labels_and_format():
    assert units.unit_label("stress", "US") == "psi"
    assert units.format_value("force", 12500.0, "SI") == "12.5 kN"


def test_unknown_unit_raises():
    with pytest.raises(KeyError):
        units.to_si("furlongs", 1)
