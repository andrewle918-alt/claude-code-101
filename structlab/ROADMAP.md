# Roadmap

Legend: [x] done, [ ] to do

- [x] **Phase 1: Foundation.** Structure, data model, JSON I/O, units, materials/sections, pytest.
- [x] **Phase 2: 2D truss and beam solver + tests.** Stiffness method, reactions, member forces,
      diagnostics, CLI demo, validation tests (triangle truss, axial bar, cantilever, SS beam, equilibrium).
- [ ] **Phase 3: 2D GUI.** Builder, supports/loads, result overlays, results table, deformation and load sliders.
- [ ] **Phase 4: 2D frames and diagrams.** Frame elements, V/M/N diagrams, releases, distributed loads, teaching mode.
- [ ] **Phase 5: Materials and stress.** Stress/FoS maps, buckling, material comparison.
- [ ] **Phase 6: 3D.** 3D truss/frame, viewport, loads/supports, overlays.
- [ ] **Phase 7: Machines.** Rigid-body solver, FBDs, mechanical advantage, posing.
- [ ] **Phase 8: Advanced behavior.** Plasticity, fatigue, thermal, optional geometric nonlinearity.
- [ ] **Phase 9: Polish.** Templates, export, performance, user guide.

## Known gaps / notes
- Not handled by the Phase 2 solver: end releases (Phase 4), cables (tension-only), rigid links (Phase 7),
  buckling status (Phase 5), 3D (Phase 6). These raise a clear `UnsupportedError`.
- The 3D tripod and Euler column validation tests belong to Phases 6 and 8 respectively.
- Truss bars carrying member loads (e.g. self-weight) have the load lumped to their end nodes.
- Stiffness matrix is assembled dense; a sparse solve is used above 1500 free DOFs (performance pass in Phase 9).
- Unsymmetric sections (angle, channel) ignore the product of inertia.
- W-shape properties are computed from nominal dimensions (fillets neglected), ~1-3% below AISC tables.
- Undo/redo command stack (`core/commands.py`) is planned for Phase 3.
