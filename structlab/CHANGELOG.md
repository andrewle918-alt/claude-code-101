# Changelog

## Unreleased

### Phase 2: 2D truss, beam and frame solver
- Direct stiffness solver `solve(model)` for 2D trusses, beams and frames (Euler-Bernoulli),
  in `structlab/solver/` (elements, assembly, diagnostics, recovery, api).
- Supports: pin, roller, fixed, inclined rollers, settlements, springs.
  Loads: nodal forces/moments, uniform and linearly varying member loads (local or global axes),
  self-weight, uniform temperature change.
- Results: reactions, displacements, member end forces (N, V, M), axial/bending stress, strain,
  elongation, factor of safety against yield, exact member diagrams (`member_diagram`).
- Diagnostics: degree of static indeterminacy, mechanism/instability detection with plain-language
  errors, global equilibrium check after every solve, large-displacement warning.
- CLI (`python -m structlab.cli`), 5 textbook example models in `examples/`, and
  `examples/validation_report.py` (solver vs. hand calculations).
- Validation tests: triangle truss, axial bar, cantilever, simply supported UDL, propped cantilever,
  triangular load, springs, settlement, inclined roller, thermal, self-weight, mechanism detection.

### Phase 1: Foundation
- Project structure (`structlab/` package, `tests/`, `examples/`), `requirements.txt`, `pyproject.toml`.
- Plain-data model: `Node`, `Member` (truss/frame/link/cable, end releases, K factor),
  `Support` (pin/roller/fixed 2D and 3D, inclined roller angle, settlement, springs),
  `NodalLoad`, `MemberLoad` (uniform/linear), `ThermalLoad`, `Model` with `validate()`.
- JSON save/load with `format_version` (human-readable, SI inside).
- `units.py`: SI and US customary conversion in one module.
- Material library (14 materials, editable JSON, typical values with sources and warnings).
- Cross-section library: round bar/tube, rectangular bar/tube, I-beam, 7 W-shapes, channel,
  angle, custom; properties computed from dimensions.
- 23 pytest tests (units, model/IO, materials, sections).
