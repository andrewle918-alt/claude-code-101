"""Save / load models as human-readable JSON."""
from __future__ import annotations

import json
from pathlib import Path

from ..core.model import Model


def save_model(model: Model, path: str | Path) -> None:
    """Write ``model`` to ``path`` as indented JSON (SI units inside)."""
    Path(path).write_text(json.dumps(model.to_dict(), indent=2) + "\n", encoding="utf-8")


def load_model(path: str | Path) -> Model:
    """Read a model JSON file written by :func:`save_model`."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Model.from_dict(data)
