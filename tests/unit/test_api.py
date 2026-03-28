"""Tests for the public Python library API."""
from polarize import discover, validate, profile


def test_discover_returns_dict(groupby_agg_dir):
    input_file = str(groupby_agg_dir / "input.py")
    report = discover(input_file, threshold="high")
    assert isinstance(report, dict)
    assert "operations" in report
    assert "summary" in report


def test_validate_returns_dict(tmp_path):
    script = tmp_path / "script.py"
    script.write_text('import polars\nprint("ok")\n')
    result = validate(original=str(script), converted=str(script))
    assert isinstance(result, dict)
    assert result["status"] == "pass"


def test_profile_returns_dict(tmp_path):
    script = tmp_path / "script.py"
    script.write_text('print("ok")\n')
    result = profile(original=str(script), converted=str(script), runs=2)
    assert isinstance(result, dict)
    assert "original_time_s" in result
    assert "time_improvement_pct" in result


def test_discover_with_threshold(groupby_agg_dir):
    input_file = str(groupby_agg_dir / "input.py")
    report_high = discover(input_file, threshold="high")
    report_low = discover(input_file, threshold="low")
    assert len(report_low["operations"]) >= len(report_high["operations"])


def test_validate_with_script_args(tmp_path):
    script = tmp_path / "script.py"
    script.write_text('import polars\nimport sys\nprint(sys.argv[1])\n')
    result = validate(
        original=str(script), converted=str(script), script_args=["test_arg"],
    )
    assert result["status"] == "pass"


def test_profile_with_script_args(tmp_path):
    script = tmp_path / "script.py"
    script.write_text('import sys\nprint(sys.argv[1])\n')
    result = profile(
        original=str(script), converted=str(script),
        runs=2, script_args=["test_arg"],
    )
    assert result["original_time_s"] > 0
