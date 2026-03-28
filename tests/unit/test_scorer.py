"""Tests for compute-weight scoring."""
from polarize.discovery.analyzer import PandasOperation
from polarize.discovery.scorer import score_operations


def _op(operation: str, line: int = 1, in_loop: bool = False) -> PandasOperation:
    return PandasOperation(
        operation=operation, line=line, code=f"df.{operation}()", in_loop=in_loop,
    )


def test_groupby_is_high():
    ops = [_op("groupby")]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "high"


def test_merge_is_high():
    ops = [_op("merge")]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "high"


def test_sort_values_is_high():
    ops = [_op("sort_values")]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "high"


def test_apply_is_high():
    ops = [_op("apply")]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "high"


def test_fillna_is_medium():
    ops = [_op("fillna")]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "medium"


def test_drop_duplicates_is_medium():
    ops = [_op("drop_duplicates")]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "medium"


def test_head_is_low():
    ops = [_op("head")]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "low"


def test_rename_is_low():
    ops = [_op("rename")]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "low"


def test_loop_promotes_medium_to_high():
    ops = [_op("fillna", in_loop=True)]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "high"


def test_loop_promotes_low_to_medium():
    ops = [_op("head", in_loop=True)]
    scored = score_operations(ops)
    assert scored[0].compute_weight == "medium"


def test_sorted_by_score_descending():
    ops = [_op("head", line=1), _op("fillna", line=2), _op("groupby", line=3)]
    scored = score_operations(ops)
    weights = [s.compute_weight for s in scored]
    assert weights == ["high", "medium", "low"]


def test_suggested_order_is_by_score():
    ops = [_op("head", line=10), _op("groupby", line=5), _op("fillna", line=8)]
    scored = score_operations(ops)
    lines = [s.line for s in scored]
    assert lines == [5, 8, 10]
