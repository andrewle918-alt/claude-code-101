from pathlib import Path

import pytest

from structlab.cli import main
from structlab.io import load_model
from structlab.solver import solve
from structlab.templates.textbook import EXAMPLES

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_example_json_exists_matches_builder_and_solves(name):
    path = EXAMPLES_DIR / f"{name}.json"
    assert path.exists(), "run: python examples/build_examples.py"
    model = load_model(path)
    assert model.to_dict() == EXAMPLES[name]()[0].to_dict()      # file is up to date
    assert solve(model).diagnostics.equilibrium_ok


def test_cli_runs_and_reports_errors(tmp_path, capsys):
    assert main([str(EXAMPLES_DIR / "01_triangle_truss.json"), "--units", "US"]) == 0
    out = capsys.readouterr().out
    assert "statically determinate" in out and "lbf" in out
    # a model with no section -> solver error, exit status 1
    from structlab.core import Model, Support
    from structlab.io import save_model
    m = Model()
    a, b = m.add_node(0, 0), m.add_node(1, 0)
    m.add_member(a.id, b.id)
    m.add_support(Support.pin2d(a.id))
    save_model(m, tmp_path / "bad.json")
    assert main([str(tmp_path / "bad.json")]) == 1
    assert "no cross-section" in capsys.readouterr().err
