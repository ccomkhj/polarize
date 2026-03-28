"""AST-based pandas operation detection."""
from __future__ import annotations

import ast
import dataclasses
from typing import Optional


@dataclasses.dataclass
class ReadCall:
    """A pandas read_* call detected in source."""
    method: str
    line: int
    code: str


@dataclasses.dataclass
class PandasOperation:
    """A pandas operation detected in source."""
    operation: str
    line: int
    code: str
    in_loop: bool = False


@dataclasses.dataclass
class AnalysisResult:
    """Result of analyzing a Python source file for pandas usage."""
    pandas_alias: Optional[str]
    operations: list[PandasOperation]
    read_calls: list[ReadCall]


# Operations we track — maps method name to canonical operation name
TRACKED_OPS = {
    "groupby": "groupby",
    "merge": "merge",
    "join": "join",
    "apply": "apply",
    "sort_values": "sort_values",
    "sort_index": "sort_index",
    "pivot_table": "pivot_table",
    "melt": "melt",
    "concat": "concat",
    "fillna": "fillna",
    "drop_duplicates": "drop_duplicates",
    "value_counts": "value_counts",
    "agg": "agg",
    "aggregate": "agg",
    "head": "head",
    "tail": "tail",
    "rename": "rename",
}


class _PandasVisitor(ast.NodeVisitor):
    """Walks AST to find pandas operations."""

    def __init__(self, source_lines: list[str]) -> None:
        self.source_lines = source_lines
        self.pandas_alias: Optional[str] = None
        self.operations: list[PandasOperation] = []
        self.read_calls: list[ReadCall] = []
        self._loop_depth = 0

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "pandas":
                self.pandas_alias = alias.asname or "pandas"
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            code = self.source_lines[node.lineno - 1].strip()

            # Check for pd.read_* calls
            if (
                isinstance(node.func.value, ast.Name)
                and self.pandas_alias
                and node.func.value.id == self.pandas_alias
                and method_name.startswith("read_")
            ):
                self.read_calls.append(ReadCall(
                    method=method_name,
                    line=node.lineno,
                    code=code,
                ))

            # Check for pd.concat (called on the module, not a DataFrame)
            if (
                isinstance(node.func.value, ast.Name)
                and self.pandas_alias
                and node.func.value.id == self.pandas_alias
                and method_name == "concat"
            ):
                self.operations.append(PandasOperation(
                    operation="concat",
                    line=node.lineno,
                    code=code,
                    in_loop=self._loop_depth > 0,
                ))

            # Check for DataFrame method calls (tracked ops)
            if method_name in TRACKED_OPS and method_name != "concat":
                self.operations.append(PandasOperation(
                    operation=TRACKED_OPS[method_name],
                    line=node.lineno,
                    code=code,
                    in_loop=self._loop_depth > 0,
                ))

        self.generic_visit(node)


def analyze_source(source: str) -> AnalysisResult:
    """Analyze Python source code for pandas operations."""
    tree = ast.parse(source)
    source_lines = source.splitlines()
    visitor = _PandasVisitor(source_lines)
    visitor.visit(tree)
    return AnalysisResult(
        pandas_alias=visitor.pandas_alias,
        operations=visitor.operations,
        read_calls=visitor.read_calls,
    )


def analyze_file(file_path: str) -> AnalysisResult:
    """Analyze a Python file for pandas operations."""
    with open(file_path) as f:
        source = f.read()
    return analyze_source(source)
