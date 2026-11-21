"""Solver exceptions. Each carries a plain-language message: the solver never
returns garbage silently, it raises one of these instead."""
from __future__ import annotations


class SolverError(Exception):
    """Base class for every problem the solver reports."""


class ModelError(SolverError):
    """The model data is inconsistent or incomplete (missing section, bad node, ...)."""

    def __init__(self, problems: list[str] | str) -> None:
        self.problems = [problems] if isinstance(problems, str) else list(problems)
        super().__init__("Model problems:\n  - " + "\n  - ".join(self.problems))


class UnsupportedError(SolverError):
    """A feature that exists in the data model but is not solved yet (later phase)."""


class InstabilityError(SolverError):
    """The structure is a mechanism, or is not supported well enough to resist loads."""

    def __init__(self, message: str, diagnostics: "object | None" = None) -> None:
        self.diagnostics = diagnostics
        super().__init__(message)
