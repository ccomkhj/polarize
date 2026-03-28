"""Integration tests: validator with real fixture pairs."""
import subprocess
import sys

from polarize import validate


def test_groupby_agg_fixture_equivalence(groupby_agg_dir):
    data_path = str(groupby_agg_dir / "data" / "sales.csv")
    result = validate(
        original=str(groupby_agg_dir / "input.py"),
        converted=str(groupby_agg_dir / "expected.py"),
        script_args=[data_path],
    )
    assert result["status"] == "pass", f"Validation failed: {result['checks']}"


def test_merge_join_fixture_equivalence(merge_join_dir):
    orders = str(merge_join_dir / "data" / "orders.csv")
    customers = str(merge_join_dir / "data" / "customers.csv")
    result = validate(
        original=str(merge_join_dir / "input.py"),
        converted=str(merge_join_dir / "expected.py"),
        script_args=[orders, customers],
    )
    assert result["status"] == "pass", f"Validation failed: {result['checks']}"


def test_sort_values_fixture_equivalence(sort_values_dir):
    data_path = str(sort_values_dir / "data" / "events.csv")
    result = validate(
        original=str(sort_values_dir / "input.py"),
        converted=str(sort_values_dir / "expected.py"),
        script_args=[data_path],
    )
    assert result["status"] == "pass", f"Validation failed: {result['checks']}"


def test_apply_func_fixture_equivalence(apply_func_dir):
    data_path = str(apply_func_dir / "data" / "transactions.csv")
    result = validate(
        original=str(apply_func_dir / "input.py"),
        converted=str(apply_func_dir / "expected.py"),
        script_args=[data_path],
    )
    assert result["status"] == "pass", f"Validation failed: {result['checks']}"


def test_chained_ops_fixture_equivalence(chained_ops_dir):
    data_path = str(chained_ops_dir / "data" / "logs.csv")
    result = validate(
        original=str(chained_ops_dir / "input.py"),
        converted=str(chained_ops_dir / "expected.py"),
        script_args=[data_path],
    )
    assert result["status"] == "pass", f"Validation failed: {result['checks']}"


def test_loop_groupby_fixture_equivalence(loop_groupby_dir):
    data_path = str(loop_groupby_dir / "data" / "metrics.csv")
    result = validate(
        original=str(loop_groupby_dir / "input.py"),
        converted=str(loop_groupby_dir / "expected.py"),
        script_args=[data_path],
    )
    assert result["status"] == "pass", f"Validation failed: {result['checks']}"


def test_validation_catches_bad_conversion(groupby_agg_dir, tmp_path):
    bad_converted = tmp_path / "bad.py"
    bad_converted.write_text('print("wrong output")\n')
    data_path = str(groupby_agg_dir / "data" / "sales.csv")
    result = validate(
        original=str(groupby_agg_dir / "input.py"),
        converted=str(bad_converted),
        script_args=[data_path],
    )
    assert result["status"] == "fail"
