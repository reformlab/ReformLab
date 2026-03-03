"""Statistical fusion methods library for population generation.

Provides the ``MergeMethod`` protocol for dataset fusion, supporting
types (``MergeConfig``, ``MergeAssumption``, ``MergeResult``), and
concrete implementations starting with ``UniformMergeMethod``.

Implements Story 11.4 (MergeMethod protocol and uniform distribution).
References FR38 (statistical methods library) and FR39 (merge method
selection with plain-language explanations).
"""

from __future__ import annotations

from reformlab.population.methods.base import (
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.errors import (
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.uniform import UniformMergeMethod

__all__ = [
    "MergeAssumption",
    "MergeConfig",
    "MergeError",
    "MergeMethod",
    "MergeResult",
    "MergeValidationError",
    "UniformMergeMethod",
]
