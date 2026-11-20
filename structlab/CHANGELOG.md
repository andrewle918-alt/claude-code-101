# Changelog

## Unreleased

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
