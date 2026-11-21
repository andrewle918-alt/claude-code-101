# StructLab

A Python desktop learning tool for statics, mechanics of materials, and machine design:
build trusses, beams, frames and simple machines (2D and 3D), apply loads and supports,
analyze with the direct stiffness method, and visualize forces, stresses, and deformation.

**Status:** Phases 1-2 complete (foundation + 2D truss/beam/frame solver with a command-line demo). The GUI arrives in Phase 3.
See `ROADMAP.md` and `CHANGELOG.md`.

## Install

```bash
cd structlab
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

Python 3.11+ is required. (PySide6, PyVista etc. are only needed from Phase 3 onward.)

## Run the tests

```bash
pytest -q
```

## Try what exists now (Phase 1)

```python
from structlab.core import Model, Support, NodalLoad
from structlab.io import save_model, load_model
from structlab.materials import default_library, make_section
from structlab import units

m = Model(name="triangle")
a, b, c = m.add_node(0, 0), m.add_node(4, 0), m.add_node(2, 3)
for i, j in [(a.id, b.id), (b.id, c.id), (c.id, a.id)]:
    m.add_member(i, j, material="A36 Steel",
                 section={"kind": "round_bar", "params": {"d": 0.02}})
m.add_support(Support.pin2d(a.id))
m.add_support(Support.roller2d(b.id))
m.add_nodal_load(NodalLoad(c.id, force=(0, -10_000, 0)))
print(m.validate())                       # [] means the data is consistent
save_model(m, "triangle.json")

print(make_section("w_shape", name="W8x31").Iz)          # m^4
print(default_library().get("Aluminum 6061-T6").yield_strength)  # Pa
print(units.format_value("stress", 276e6, "US"))         # 4.003e+04 psi
```

## Solve a model from the command line (Phase 2)

```bash
python examples/build_examples.py                      # (re)writes examples/*.json
python -m structlab.cli examples/01_triangle_truss.json
python -m structlab.cli examples/05_propped_cantilever_udl.json --units US
python examples/validation_report.py                   # solver vs. hand calculations
```

or from Python: `results = solve(model)` (see `structlab/solver/api.py`).
The solver raises a plain-language error for mechanisms, missing supports and bad data, and
runs a global equilibrium check after every solve (a failure is shown as a warning).

Example models (open them and compare to your own work; the hand-check values are in each file's `notes`):

| file | hand result |
|---|---|
| `01_triangle_truss` | F_AB=+3.75 kN, F_BC=F_CA=-6.25 kN, R=5 kN each |
| `02_axial_bar` | delta = PL/AE = 1.0 mm |
| `03_cantilever_beam` | tip deflection PL^3/3EI = 5.625 mm, M = PL = 30 kN*m |
| `04_simply_supported_beam_udl` | M_max = wL^2/8 = 22.5 kN*m, delta = 5wL^4/384EI = 5.273 mm |
| `05_propped_cantilever_udl` | R_prop = 3wL/8 = 11.25 kN, M_fixed = wL^2/8 (indeterminate) |

## Conventions (also shown in the in-app help from Phase 3)

- **Internal units are base SI** (m, N, N·m, Pa, kg, K). Only `structlab/units.py`
  converts to/from display units (SI or US customary).
- **Tension is positive**, compression negative.
- **DOF order:** `(ux, uy, uz, rx, ry, rz)`; 2D models use `ux, uy, rz`.
- **Shear V** positive = upward on the left face of a segment; **moment M** positive = sagging.
- **Member local x axis** points from node `i` to node `j`.
- **Section axes:** `Iz = ∫y² dA` is the in-plane (strong) axis for 2D beams.
- Material and section values are **typical handbook values, not design-certified.**
  The material library is plain JSON (`structlab/materials/materials.json`): edit or extend it.

## Layout

```
structlab/
  core/       plain-data model classes (no GUI/solver imports)
  materials/  material library (JSON) and cross-section library
  io/         JSON save/load (CSV/PNG export later)
  solver/     FEM + equilibrium solvers (Phase 2+)
  viz/ gui/ templates/   later phases
tests/  examples/
```
