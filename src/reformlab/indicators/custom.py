"""Custom derived indicator formulas for ReformLab.

Story 4.6: Implement Custom Derived Indicator Formulas

This module provides:
- CustomFormulaConfig: Configuration for custom derived formulas
- FormulaValidationError: Exception for invalid formula syntax or references
- apply_custom_formula: Apply a single custom formula to indicator results
- apply_custom_formulas: Apply multiple custom formulas in sequence
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.indicators.types import IndicatorResult


class FormulaValidationError(ValueError):
    """Raised when a custom formula has invalid syntax or references.

    Attributes:
        message: Error description.
        position: Character position of the error in the expression.
        suggestion: Optional suggested correction.
    """

    def __init__(
        self,
        message: str,
        position: int | None = None,
        suggestion: str | None = None,
    ):
        """Initialize FormulaValidationError.

        Args:
            message: Error description.
            position: Character position of the error.
            suggestion: Optional suggested correction.
        """
        self.position = position
        self.suggestion = suggestion
        super().__init__(message)


@dataclass
class CustomFormulaConfig:
    """Configuration for a custom derived indicator formula.

    Attributes:
        source_field: Existing indicator field_name to read metrics from.
        output_metric: Name of the derived metric to create.
        expression: Formula expression string (e.g., "revenue - cost").
        description: Human-readable description for documentation/governance.
    """

    source_field: str
    output_metric: str
    expression: str
    description: str = ""


class _TokenType(Enum):
    """Token types for formula parsing."""

    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"


@dataclass
class _Token:
    """Token for formula parsing."""

    type: _TokenType
    value: str | float
    position: int


class _Tokenizer:
    """Tokenizer for formula expressions."""

    def __init__(self, expression: str):
        """Initialize tokenizer.

        Args:
            expression: Formula expression string.
        """
        self.expression = expression
        self.position = 0
        self.current_char = expression[0] if expression else None

    def _advance(self) -> None:
        """Advance to next character."""
        self.position += 1
        if self.position < len(self.expression):
            self.current_char = self.expression[self.position]
        else:
            self.current_char = None

    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.current_char is not None and self.current_char.isspace():
            self._advance()

    def _read_number(self) -> _Token:
        """Read numeric token (integer or float)."""
        start_pos = self.position
        num_str = ""
        while self.current_char is not None and (
            self.current_char.isdigit() or self.current_char == "."
        ):
            num_str += self.current_char
            self._advance()
        try:
            value = float(num_str)
        except ValueError as e:
            msg = f"Invalid number format: {num_str!r}"
            raise FormulaValidationError(msg, position=start_pos) from e
        return _Token(_TokenType.NUMBER, value, start_pos)

    def _read_identifier(self) -> _Token:
        """Read identifier token (metric name)."""
        start_pos = self.position
        ident = ""
        while self.current_char is not None and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
            ident += self.current_char
            self._advance()
        return _Token(_TokenType.IDENTIFIER, ident, start_pos)

    def tokenize(self) -> list[_Token]:
        """Tokenize the expression.

        Returns:
            List of tokens.

        Raises:
            FormulaValidationError: If invalid characters are encountered.
        """
        tokens: list[_Token] = []

        while self.current_char is not None:
            self._skip_whitespace()

            if self.current_char is None:
                break

            if self.current_char.isdigit() or self.current_char == ".":
                tokens.append(self._read_number())
            elif self.current_char.isalpha() or self.current_char == "_":
                tokens.append(self._read_identifier())
            elif self.current_char == "+":
                tokens.append(_Token(_TokenType.PLUS, "+", self.position))
                self._advance()
            elif self.current_char == "-":
                tokens.append(_Token(_TokenType.MINUS, "-", self.position))
                self._advance()
            elif self.current_char == "*":
                tokens.append(_Token(_TokenType.MULTIPLY, "*", self.position))
                self._advance()
            elif self.current_char == "/":
                tokens.append(_Token(_TokenType.DIVIDE, "/", self.position))
                self._advance()
            elif self.current_char == "(":
                tokens.append(_Token(_TokenType.LPAREN, "(", self.position))
                self._advance()
            elif self.current_char == ")":
                tokens.append(_Token(_TokenType.RPAREN, ")", self.position))
                self._advance()
            else:
                msg = (
                    f"Invalid character in expression: {self.current_char!r} "
                    f"at position {self.position}"
                )
                raise FormulaValidationError(msg, position=self.position)

        tokens.append(_Token(_TokenType.EOF, "", self.position))
        return tokens


class _ASTNode:
    """Base class for AST nodes."""


@dataclass
class _NumberNode(_ASTNode):
    """AST node for numeric constants."""

    value: float


@dataclass
class _IdentifierNode(_ASTNode):
    """AST node for metric references."""

    name: str


@dataclass
class _BinaryOpNode(_ASTNode):
    """AST node for binary operations."""

    operator: _TokenType
    left: _ASTNode
    right: _ASTNode


class _Parser:
    """Recursive descent parser for formula expressions.

    Grammar:
        expression: term ((PLUS | MINUS) term)*
        term: factor ((MULTIPLY | DIVIDE) factor)*
        factor: NUMBER | IDENTIFIER | LPAREN expression RPAREN
    """

    def __init__(self, tokens: list[_Token]):
        """Initialize parser.

        Args:
            tokens: List of tokens from tokenizer.
        """
        self.tokens = tokens
        self.position = 0
        self.current_token = tokens[0] if tokens else _Token(_TokenType.EOF, "", 0)

    def _advance(self) -> None:
        """Advance to next token."""
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]

    def _expect(self, token_type: _TokenType) -> _Token:
        """Expect a specific token type and advance.

        Args:
            token_type: Expected token type.

        Returns:
            The consumed token.

        Raises:
            FormulaValidationError: If current token doesn't match expected type.
        """
        if self.current_token.type != token_type:
            msg = (
                f"Expected {token_type.value}, "
                f"got {self.current_token.type.value!r} "
                f"at position {self.current_token.position}"
            )
            raise FormulaValidationError(msg, position=self.current_token.position)
        token = self.current_token
        self._advance()
        return token

    def parse(self) -> _ASTNode:
        """Parse tokens into AST.

        Returns:
            Root AST node.

        Raises:
            FormulaValidationError: If syntax errors are encountered.
        """
        result = self._parse_expression()
        if self.current_token.type != _TokenType.EOF:
            msg = (
                f"Unexpected token after expression: "
                f"{self.current_token.type.value!r} "
                f"at position {self.current_token.position}"
            )
            raise FormulaValidationError(msg, position=self.current_token.position)
        return result

    def _parse_expression(self) -> _ASTNode:
        """Parse expression: term ((PLUS | MINUS) term)*."""
        left = self._parse_term()

        while self.current_token.type in (_TokenType.PLUS, _TokenType.MINUS):
            operator = self.current_token.type
            self._advance()
            right = self._parse_term()
            left = _BinaryOpNode(operator, left, right)

        return left

    def _parse_term(self) -> _ASTNode:
        """Parse term: factor ((MULTIPLY | DIVIDE) factor)*."""
        left = self._parse_factor()

        while self.current_token.type in (_TokenType.MULTIPLY, _TokenType.DIVIDE):
            operator = self.current_token.type
            self._advance()
            right = self._parse_factor()
            left = _BinaryOpNode(operator, left, right)

        return left

    def _parse_factor(self) -> _ASTNode:
        """Parse factor: NUMBER | IDENTIFIER | LPAREN expression RPAREN."""
        token = self.current_token

        if token.type == _TokenType.NUMBER:
            self._advance()
            return _NumberNode(float(token.value))

        if token.type == _TokenType.IDENTIFIER:
            self._advance()
            return _IdentifierNode(str(token.value))

        if token.type == _TokenType.LPAREN:
            self._advance()
            node = self._parse_expression()
            self._expect(_TokenType.RPAREN)
            return node

        msg = (
            f"Expected number, identifier, or '(', "
            f"got {token.type.value!r} at position {token.position}"
        )
        raise FormulaValidationError(msg, position=token.position)


def _parse_formula(expression: str) -> _ASTNode:
    """Parse formula expression into AST.

    Args:
        expression: Formula expression string.

    Returns:
        Root AST node.

    Raises:
        FormulaValidationError: If syntax errors are encountered.
    """
    if not expression.strip():
        msg = "Formula expression cannot be empty"
        raise FormulaValidationError(msg)

    tokenizer = _Tokenizer(expression)
    tokens = tokenizer.tokenize()
    parser = _Parser(tokens)
    return parser.parse()


def _safe_divide(numerator: pa.Array, denominator: pa.Array) -> pa.Array:
    """Divide with null for zero denominator.

    Args:
        numerator: Numerator array.
        denominator: Denominator array.

    Returns:
        Result array with nulls for zero denominators.
    """
    is_zero = pc.equal(denominator, 0.0)
    result = pc.divide(numerator, denominator)
    return pc.if_else(is_zero, pa.scalar(None, type=pa.float64()), result)


def _evaluate_ast(
    node: _ASTNode,
    metric_arrays: dict[str, pa.Array],
) -> pa.Array:
    """Evaluate AST node to PyArrow array.

    Args:
        node: AST node to evaluate.
        metric_arrays: Mapping of metric names to PyArrow arrays.

    Returns:
        PyArrow array with evaluation result.

    Raises:
        FormulaValidationError: If metric references are invalid.
    """
    if isinstance(node, _NumberNode):
        # Create a scalar array with the constant value
        return pa.array([node.value], type=pa.float64())

    if isinstance(node, _IdentifierNode):
        if node.name not in metric_arrays:
            available = ", ".join(sorted(metric_arrays))
            msg = f"Metric '{node.name}' not found. Available metrics: {available}"
            raise FormulaValidationError(msg)
        return metric_arrays[node.name]

    if isinstance(node, _BinaryOpNode):
        left = _evaluate_ast(node.left, metric_arrays)
        right = _evaluate_ast(node.right, metric_arrays)

        # Handle scalar constants: broadcast to match array length
        if left.type == pa.float64() and len(left) == 1:
            if len(right) > 1:
                left = pa.array([left[0].as_py()] * len(right), type=pa.float64())
        if right.type == pa.float64() and len(right) == 1:
            if len(left) > 1:
                right = pa.array([right[0].as_py()] * len(left), type=pa.float64())

        if node.operator == _TokenType.PLUS:
            return pc.add(left, right)
        if node.operator == _TokenType.MINUS:
            return pc.subtract(left, right)
        if node.operator == _TokenType.MULTIPLY:
            return pc.multiply(left, right)
        if node.operator == _TokenType.DIVIDE:
            return _safe_divide(left, right)

        msg = f"Unsupported operator: {node.operator}"
        raise FormulaValidationError(msg)

    msg = f"Unsupported AST node type: {type(node)}"
    raise FormulaValidationError(msg)


def _extract_metric_arrays(
    table: pa.Table,
    source_field: str,
) -> dict[str, dict[tuple[Any, ...], pa.Array]]:
    """Extract metric arrays from indicator table for each grouping key.

    Args:
        table: Long-form indicator table with columns:
            field_name, grouping keys (decile/region), year, metric, value.
        source_field: Field name to filter on.

    Returns:
        Nested dictionary: {metric_name: {grouping_key_tuple: array}}
        where grouping_key_tuple is (decile|region, year) or (year,) for fiscal.

    Raises:
        FormulaValidationError: If source_field is not found in table.
    """
    if "field_name" not in table.column_names:
        msg = "Indicator table missing 'field_name' column"
        raise FormulaValidationError(msg)

    # Filter table to source_field
    field_mask = pc.equal(table["field_name"], source_field)
    filtered = table.filter(field_mask)

    if filtered.num_rows == 0:
        available_fields = pc.unique(table["field_name"]).to_pylist()
        msg = (
            f"Source field '{source_field}' not found in indicator table. "
            f"Available fields: {available_fields}"
        )
        raise FormulaValidationError(msg)

    # Determine grouping columns
    grouping_cols: list[str] = []
    if "decile" in filtered.column_names:
        grouping_cols.append("decile")
    if "region" in filtered.column_names:
        grouping_cols.append("region")
    if "year" in filtered.column_names:
        grouping_cols.append("year")

    # Build nested dictionary: {metric: {grouping_key: array}}
    result: dict[str, dict[tuple[Any, ...], pa.Array]] = {}

    for row_idx in range(filtered.num_rows):
        metric = filtered["metric"][row_idx].as_py()
        value = filtered["value"][row_idx].as_py()

        # Build grouping key tuple
        grouping_key = tuple(
            filtered[col][row_idx].as_py() for col in grouping_cols
        )

        if metric not in result:
            result[metric] = {}
        if grouping_key not in result[metric]:
            result[metric][grouping_key] = []

        result[metric][grouping_key].append(value)

    # Convert lists to PyArrow arrays
    for metric in result:
        for grouping_key in result[metric]:
            result[metric][grouping_key] = pa.array(
                result[metric][grouping_key], type=pa.float64()
            )

    return result


class _DerivedIndicatorResult(IndicatorResult):
    """Specialized IndicatorResult that extends to_table() with derived metrics.

    This class wraps an IndicatorResult and adds derived metric rows when
    to_table() is called.
    """

    def __init__(
        self,
        base_result: IndicatorResult,
        derived_table: pa.Table | None = None,
    ):
        """Initialize _DerivedIndicatorResult.

        Args:
            base_result: Original IndicatorResult.
            derived_table: PyArrow table with only derived metric rows.
        """
        super().__init__(
            indicators=base_result.indicators,
            metadata=base_result.metadata,
            warnings=base_result.warnings,
            excluded_count=base_result.excluded_count,
            unmatched_count=base_result.unmatched_count,
        )
        self._base_result = base_result
        self._derived_table = derived_table

    def to_table(self) -> pa.Table:
        """Return indicator table with derived metric rows appended.

        Returns:
            PyArrow table with original and derived metrics.
        """
        base_table = self._base_result.to_table()
        if self._derived_table is None or self._derived_table.num_rows == 0:
            return base_table
        return pa.concat_tables([base_table, self._derived_table])


def apply_custom_formula(
    result: IndicatorResult,
    formula: CustomFormulaConfig,
) -> IndicatorResult:
    """Apply a custom formula to indicator results.

    Creates a new IndicatorResult with derived metric rows added to the table.
    The original indicator values are preserved unchanged.

    Args:
        result: IndicatorResult from any indicator computation.
        formula: Custom formula configuration.

    Returns:
        New IndicatorResult with derived metric added. The derived metrics
        are included when calling to_table().

    Raises:
        FormulaValidationError: If formula syntax is invalid or metric
            references cannot be resolved.
    """
    # Parse formula
    ast = _parse_formula(formula.expression)

    # Convert to table (handles derived results too)
    table = result.to_table()

    if table.num_rows == 0:
        # Empty result, return as-is with formula metadata
        metadata = dict(result.metadata)
        if "custom_formulas" not in metadata:
            metadata["custom_formulas"] = []
        metadata["custom_formulas"].append({
            "source_field": formula.source_field,
            "output_metric": formula.output_metric,
            "expression": formula.expression,
            "description": formula.description,
        })
        return IndicatorResult(
            indicators=result.indicators,
            metadata=metadata,
            warnings=result.warnings,
            excluded_count=result.excluded_count,
            unmatched_count=result.unmatched_count,
        )

    # Extract metric arrays per grouping key
    metric_data = _extract_metric_arrays(table, formula.source_field)

    # Validate that all metrics have the same grouping keys
    all_grouping_keys: set[tuple[Any, ...]] = set()
    for metric in metric_data.values():
        all_grouping_keys.update(metric.keys())

    # Determine table schema for derived rows
    derived_rows: dict[str, list[Any]] = {col: [] for col in table.column_names}

    for grouping_key in sorted(all_grouping_keys):
        # Build metric_arrays for this grouping key
        metric_arrays: dict[str, pa.Array] = {}
        for metric_name, keys_dict in metric_data.items():
            if grouping_key in keys_dict:
                metric_arrays[metric_name] = keys_dict[grouping_key]

        if not metric_arrays:
            # No metrics available for this grouping key, skip
            continue

        # Evaluate formula
        try:
            result_array = _evaluate_ast(ast, metric_arrays)
        except FormulaValidationError:
            raise
        except Exception as e:
            msg = (
                f"Error evaluating formula '{formula.expression}' "
                f"for grouping key {grouping_key}: {e}"
            )
            raise FormulaValidationError(msg) from e

        # Aggregate result (typically should be single value per grouping key)
        if len(result_array) == 1:
            derived_value = result_array[0].as_py()
        else:
            # Should not happen in typical indicator scenarios,
            # but handle gracefully by taking mean
            derived_value = pc.mean(result_array).as_py()

        # Add row to derived_rows
        derived_rows["field_name"].append(formula.source_field)
        derived_rows["metric"].append(formula.output_metric)
        derived_rows["value"].append(derived_value)

        # Add grouping columns
        grouping_key_temp = grouping_key
        if "decile" in table.column_names:
            derived_rows["decile"].append(
                grouping_key_temp[0] if grouping_key_temp else None
            )
            grouping_key_temp = (
                grouping_key_temp[1:] if len(grouping_key_temp) > 1 else ()
            )
        if "region" in table.column_names:
            derived_rows["region"].append(
                grouping_key_temp[0] if grouping_key_temp else None
            )
            grouping_key_temp = (
                grouping_key_temp[1:] if len(grouping_key_temp) > 1 else ()
            )
        if "year" in table.column_names:
            derived_rows["year"].append(
                grouping_key_temp[0] if grouping_key_temp else None
            )

    # Create derived table with explicit schema
    if derived_rows["field_name"]:
        # Build schema matching the base table
        schema_dict: dict[str, pa.DataType] = {}
        for col_name in table.column_names:
            schema_dict[col_name] = table.schema.field(col_name).type

        # Create PyArrow arrays with explicit types
        derived_arrays = {}
        for col_name in derived_rows:
            if col_name in schema_dict:
                derived_arrays[col_name] = pa.array(
                    derived_rows[col_name],
                    type=schema_dict[col_name],
                )

        derived_table = pa.table(derived_arrays)
    else:
        derived_table = None

    # Update metadata
    metadata = dict(result.metadata)
    if "custom_formulas" not in metadata:
        metadata["custom_formulas"] = []
    metadata["custom_formulas"].append({
        "source_field": formula.source_field,
        "output_metric": formula.output_metric,
        "expression": formula.expression,
        "description": formula.description,
    })

    # Extract existing derived table if result is already a _DerivedIndicatorResult
    if isinstance(result, _DerivedIndicatorResult) and result._derived_table is not None:
        if derived_table is not None:
            combined_derived = pa.concat_tables([result._derived_table, derived_table])
        else:
            combined_derived = result._derived_table
        base_result = result._base_result
    else:
        combined_derived = derived_table
        base_result = result

    # Create new result with updated metadata
    base_with_metadata = IndicatorResult(
        indicators=base_result.indicators,
        metadata=metadata,
        warnings=result.warnings,
        excluded_count=result.excluded_count,
        unmatched_count=result.unmatched_count,
    )

    return _DerivedIndicatorResult(
        base_result=base_with_metadata,
        derived_table=combined_derived,
    )


def apply_custom_formulas(
    result: IndicatorResult,
    formulas: list[CustomFormulaConfig],
) -> IndicatorResult:
    """Apply multiple custom formulas in sequence.

    Each formula is applied in order, allowing later formulas to reference
    metrics created by earlier formulas.

    Args:
        result: IndicatorResult from any indicator computation.
        formulas: List of custom formula configurations.

    Returns:
        New IndicatorResult with all derived metrics added.

    Raises:
        FormulaValidationError: If any formula has invalid syntax or metric
            references cannot be resolved.
    """
    current_result = result
    for formula in formulas:
        current_result = apply_custom_formula(current_result, formula)
    return current_result
