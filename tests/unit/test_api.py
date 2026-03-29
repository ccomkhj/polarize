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


def test_validate_invalid_syntax_returns_failure(tmp_path):
    original = tmp_path / "original.py"
    converted = tmp_path / "converted.py"
    original.write_text('print("ok")\n')
    converted.write_text("def broken(:\n    pass\n")
    result = validate(original=str(original), converted=str(converted))
    assert result["status"] == "fail"
    assert result["checks"][0]["check"] == "syntax"


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


def test_discover_directory_recursive_returns_reports(tmp_path):
    pandas_file = tmp_path / "pandas_script.py"
    plain_file = tmp_path / "plain.py"
    pandas_file.write_text(
        'import pandas as pd\n'
        'df = pd.read_csv("data.csv")\n'
        'df = df.sort_values("id")\n'
    )
    plain_file.write_text('print("hello")\n')

    report = discover(str(tmp_path), recursive=True)
    assert report["path"] == str(tmp_path)
    assert len(report["reports"]) == 1
    assert report["reports"][0]["file"] == str(pandas_file)


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
