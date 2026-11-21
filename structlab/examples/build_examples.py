"""Write the textbook validation models to JSON files in this folder.

    python examples/build_examples.py

Each file can be solved from the command line
    python -m structlab.cli examples/01_triangle_truss.json
and (from Phase 3) opened in the GUI to compare with your own hand calculations.
"""
from pathlib import Path

from structlab.io import save_model
from structlab.templates.textbook import EXAMPLES

here = Path(__file__).parent
for name, builder in EXAMPLES.items():
    model, _ = builder()
    save_model(model, here / f"{name}.json")
    print("wrote", here / f"{name}.json")
