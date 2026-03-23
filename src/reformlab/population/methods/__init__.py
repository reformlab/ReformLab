# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Statistical fusion methods library for population generation.

Provides the ``MergeMethod`` protocol for dataset fusion, supporting
types (``MergeConfig``, ``MergeAssumption``, ``MergeResult``), and
concrete implementations: ``UniformMergeMethod``, ``IPFMergeMethod``,
and ``ConditionalSamplingMethod``.

Implements Story 11.4 (MergeMethod protocol and uniform distribution)
and Story 11.5 (IPF and conditional sampling merge methods).
References FR38 (statistical methods library) and FR39 (merge method
selection with plain-language explanations).
"""

from __future__ import annotations

from reformlab.population.methods.base import (
    IPFConstraint,
    IPFResult,
    MergeAssumption,
    MergeConfig,
    MergeMethod,
    MergeResult,
)
from reformlab.population.methods.conditional import ConditionalSamplingMethod
from reformlab.population.methods.errors import (
    MergeConvergenceError,
    MergeError,
    MergeValidationError,
)
from reformlab.population.methods.ipf import IPFMergeMethod
from reformlab.population.methods.uniform import UniformMergeMethod

__all__ = [
    "ConditionalSamplingMethod",
    "IPFConstraint",
    "IPFMergeMethod",
    "IPFResult",
    "MergeAssumption",
    "MergeConfig",
    "MergeConvergenceError",
    "MergeError",
    "MergeMethod",
    "MergeResult",
    "MergeValidationError",
    "UniformMergeMethod",
]
