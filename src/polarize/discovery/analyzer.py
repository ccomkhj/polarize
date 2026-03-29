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

PANDAS_CONSTRUCTORS = {
    "DataFrame",
    "Series",
}

CHAINED_RETURNING_METHODS = {
    "reset_index",
    "sum",
    "mean",
    "min",
    "max",
    "count",
}


class _PandasVisitor(ast.NodeVisitor):
    """Walks AST to find pandas operations."""

    def __init__(self, source_lines: list[str]) -> None:
        self.source_lines = source_lines
        self.pandas_alias: Optional[str] = None
        self.pandas_aliases: set[str] = set()
        self.imported_pandas_names: dict[str, str] = {}
        self.operations: list[PandasOperation] = []
        self.read_calls: list[ReadCall] = []
        self.pandas_symbols: set[str] = set()
        self._loop_depth = 0

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "pandas":
                local_name = alias.asname or "pandas"
                self.pandas_aliases.add(local_name)
                if self.pandas_alias is None:
                    self.pandas_alias = local_name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "pandas":
            if self.pandas_alias is None:
                self.pandas_alias = "pandas"
            for alias in node.names:
                local_name = alias.asname or alias.name
                self.imported_pandas_names[local_name] = alias.name
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_Assign(self, node: ast.Assign) -> None:
        value_is_pandas = self._is_pandas_expression(node.value)
        self.generic_visit(node)
        self._update_targets(node.targets, value_is_pandas)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        value_is_pandas = node.value is not None and self._is_pandas_expression(node.value)
        self.generic_visit(node)
        self._update_target(node.target, value_is_pandas)

    def visit_Call(self, node: ast.Call) -> None:
        code = self.source_lines[node.lineno - 1].strip()
        read_method = self._read_method_name(node)
        if read_method is not None:
            self.read_calls.append(
                ReadCall(
                    method=read_method,
                    line=node.lineno,
                    code=code,
                )
            )

        operation_name = self._tracked_operation_name(node)
        if operation_name is not None:
            self.operations.append(
                PandasOperation(
                    operation=operation_name,
                    line=node.lineno,
                    code=code,
                    in_loop=self._loop_depth > 0,
                )
            )

        self.generic_visit(node)

    def _read_method_name(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Attribute):
            if self._is_pandas_module_alias(node.func.value) and node.func.attr.startswith("read_"):
                return node.func.attr
            return None

        if isinstance(node.func, ast.Name):
            imported_name = self.imported_pandas_names.get(node.func.id)
            if imported_name is not None and imported_name.startswith("read_"):
                return imported_name

        return None

    def _tracked_operation_name(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
            imported_name = self.imported_pandas_names.get(node.func.id)
            if imported_name == "concat":
                return "concat"
            return None

        if not isinstance(node.func, ast.Attribute):
            return None

        method_name = node.func.attr
        if method_name == "concat" and self._is_pandas_module_alias(node.func.value):
            return "concat"

        if method_name not in TRACKED_OPS or not self._is_pandas_expression(node.func.value):
            return None

        return TRACKED_OPS[method_name]

    def _is_pandas_expression(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id in self.pandas_symbols

        if isinstance(node, ast.Call):
            return self._call_returns_pandas(node)

        if isinstance(node, ast.Subscript):
            return self._is_pandas_expression(node.value)

        if isinstance(node, ast.Attribute):
            return self._is_pandas_expression(node.value)

        return False

    def _call_returns_pandas(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Name):
            imported_name = self.imported_pandas_names.get(node.func.id)
            return imported_name is not None and (
                imported_name.startswith("read_")
                or imported_name == "concat"
                or imported_name in PANDAS_CONSTRUCTORS
            )

        if not isinstance(node.func, ast.Attribute):
            return False

        if self._is_pandas_module_alias(node.func.value):
            return (
                node.func.attr.startswith("read_")
                or node.func.attr == "concat"
                or node.func.attr in PANDAS_CONSTRUCTORS
            )

        return (
            self._is_pandas_expression(node.func.value)
            and (
                node.func.attr in TRACKED_OPS
                or node.func.attr in CHAINED_RETURNING_METHODS
            )
        )

    def _is_pandas_module_alias(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Name) and node.id in self.pandas_aliases

    def _update_targets(self, targets: list[ast.expr], value_is_pandas: bool) -> None:
        for target in targets:
            self._update_target(target, value_is_pandas)

    def _update_target(self, target: ast.AST, value_is_pandas: bool) -> None:
        if isinstance(target, ast.Name):
            if value_is_pandas:
                self.pandas_symbols.add(target.id)
            else:
                self.pandas_symbols.discard(target.id)
            return

        if isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._update_target(element, value_is_pandas)


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
