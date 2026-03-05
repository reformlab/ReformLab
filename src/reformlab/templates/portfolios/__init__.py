"""Policy portfolio composition and serialization.

This module provides the PolicyPortfolio frozen dataclass for composing
multiple individual policy templates into named, versioned policy packages.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
Story 12.2: Implement portfolio compatibility validation and conflict resolution
"""

from __future__ import annotations

from reformlab.templates.portfolios.composition import (
    Conflict,
    ConflictType,
    ResolutionStrategy,
    dump_portfolio,
    load_portfolio,
    resolve_conflicts,
    validate_compatibility,
)
from reformlab.templates.portfolios.exceptions import (
    PortfolioError,
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio

__all__ = [
    "Conflict",
    "ConflictType",
    "PolicyConfig",
    "PolicyPortfolio",
    "PortfolioError",
    "PortfolioValidationError",
    "PortfolioSerializationError",
    "ResolutionStrategy",
    "dump_portfolio",
    "load_portfolio",
    "resolve_conflicts",
    "validate_compatibility",
]
