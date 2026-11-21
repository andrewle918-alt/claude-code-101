"""Command-line demo:  python -m structlab.cli model.json [--units US] [--load-factor 1.5]

Loads a model JSON file, solves it and prints reactions, displacements, member
forces and the diagnostics.  Exit status 1 if the solver reports a problem.
"""
from __future__ import annotations

import argparse
import sys

from .io import load_model
from .solver import AnalysisOptions, SolverError, solve


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="structlab.cli", description="Solve a StructLab model file.")
    p.add_argument("model", help="path to a model .json file")
    p.add_argument("--units", choices=["SI", "US"], default=None,
                   help="display units (default: the units stored in the file)")
    p.add_argument("--load-factor", type=float, default=1.0, help="scale all loads (default 1.0)")
    args = p.parse_args(argv)

    model = load_model(args.model)
    try:
        results = solve(model, AnalysisOptions(load_factor=args.load_factor))
    except SolverError as exc:
        print(f"SOLVER ERROR: {exc}", file=sys.stderr)
        return 1
    print(results.summary(args.units or model.display_units))
    if model.notes:
        print("\nModel notes (hand-check values):\n  " + model.notes)
    return 0 if results.diagnostics.equilibrium_ok else 1


if __name__ == "__main__":
    sys.exit(main())
