# StructLab

A Python desktop learning tool for statics, mechanics of materials, and machine design:
build trusses, beams, frames and simple machines (2D and 3D), apply loads and supports,
analyze with the direct stiffness method, and visualize forces, stresses, and deformation.

**Status:** Phase 1 (foundation) complete. The solver arrives in Phase 2 and the GUI in Phase 3.
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

## Conventions (also shown in the in-app help from Phase 3)

- **Internal units are base SI** (m, N, N·m, Pa, kg, K). Only `structlab/units.py`
  converts to/from display units (SI or US customary).
- **Tension is positive**, compression negative.
- **DOF order:** `(ux, uy, uz, rx, ry, rz)`; 2D models use `ux, uy, rz`.
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
