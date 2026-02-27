"""Vintage subsystem error classes.

This module provides:
- VintageConfigError: Invalid vintage configuration
- VintageTransitionError: Error during vintage transition execution
"""


class VintageConfigError(Exception):
    """Invalid vintage configuration.

    Raised when vintage configuration is malformed, such as missing
    required fields, invalid parameter bounds, or unsupported asset classes.
    """


class VintageTransitionError(Exception):
    """Error during vintage transition execution.

    Raised when a vintage transition step fails, such as missing
    initial state, invalid cohort data, or rule application failures.
    """
