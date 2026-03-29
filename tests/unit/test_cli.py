"""Tests for CLI commands."""
import json

from click.testing import CliRunner

from polarize.cli import cli


def test_discover_outputs_json(groupby_agg_dir):
    runner = CliRunner()
    input_file = str(groupby_agg_dir / "input.py")
    result = runner.invoke(cli, ["discover", input_file])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["file"] == input_file
    assert len(data["operations"]) > 0


def test_discover_threshold_filter(groupby_agg_dir):
    runner = CliRunner()
    input_file = str(groupby_agg_dir / "input.py")
    result_high = runner.invoke(cli, ["discover", input_file, "--threshold", "high"])
    data_high = json.loads(result_high.output)
    result_low = runner.invoke(cli, ["discover", input_file, "--threshold", "low"])
    data_low = json.loads(result_low.output)
    assert len(data_low["operations"]) >= len(data_high["operations"])


def test_discover_text_format(groupby_agg_dir):
    runner = CliRunner()
    input_file = str(groupby_agg_dir / "input.py")
    result = runner.invoke(cli, ["discover", input_file, "--format", "text"])
    assert result.exit_code == 0
    try:
        json.loads(result.output)
        assert False, "Text format should not be valid JSON"
    except json.JSONDecodeError:
        pass


def test_discover_nonexistent_file():
    runner = CliRunner()
    result = runner.invoke(cli, ["discover", "/nonexistent/file.py"])
    assert result.exit_code == 2


def test_discover_non_pandas_file_returns_empty_report(tmp_path):
    runner = CliRunner()
    input_file = tmp_path / "plain.py"
    input_file.write_text('print("hello")\n')
    result = runner.invoke(cli, ["discover", str(input_file)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["file"] == str(input_file)
    assert data["operations"] == []
    assert data["data_sources"] == []


def test_discover_recursive_outputs_single_json_document(tmp_path):
    runner = CliRunner()
    pandas_file = tmp_path / "pandas_script.py"
    plain_file = tmp_path / "plain.py"
    pandas_file.write_text(
        'import pandas as pd\n'
        'df = pd.read_csv("data.csv")\n'
        'df = df.sort_values("id")\n'
    )
    plain_file.write_text('print("hello")\n')

    result = runner.invoke(cli, ["discover", str(tmp_path), "--recursive"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["path"] == str(tmp_path)
    assert len(data["reports"]) == 1
    assert data["reports"][0]["file"] == str(pandas_file)


def test_validate_pass(tmp_path):
    original = tmp_path / "original.py"
    converted = tmp_path / "converted.py"
    original.write_text('print("a,b")\nprint("1,2")\n')
    converted.write_text('import polars\nprint("a,b")\nprint("1,2")\n')
    runner = CliRunner()
    result = runner.invoke(cli, [
        "validate", "--original", str(original), "--converted", str(converted),
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "pass"


def test_validate_fail(tmp_path):
    original = tmp_path / "original.py"
    converted = tmp_path / "converted.py"
    original.write_text('print("1")\n')
    converted.write_text('print("2")\n')
    runner = CliRunner()
    result = runner.invoke(cli, [
        "validate", "--original", str(original), "--converted", str(converted),
    ])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["status"] == "fail"


def test_validate_syntax_error_returns_failure_json(tmp_path):
    original = tmp_path / "original.py"
    converted = tmp_path / "converted.py"
    original.write_text('print("ok")\n')
    converted.write_text("def broken(:\n    pass\n")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["validate", "--original", str(original), "--converted", str(converted)],
    )
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["status"] == "fail"
    assert data["checks"][0]["check"] == "syntax"


def test_validate_with_script_args(tmp_path):
    script = tmp_path / "script.py"
    script.write_text('import sys\nimport polars as pl\nprint(sys.argv[1])\n')
    runner = CliRunner()
    result = runner.invoke(cli, [
        "validate", "--original", str(script), "--converted", str(script),
        "--", "hello",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "pass"


def test_profile_outputs_json(tmp_path):
    script = tmp_path / "script.py"
    script.write_text('print("ok")\n')
    runner = CliRunner()
    result = runner.invoke(cli, [
        "profile", "--original", str(script), "--converted", str(script), "--runs", "2",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "original_time_s" in data
    assert "time_improvement_pct" in data
    assert data["runs"] == 2


def test_ops_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["ops"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data["operations"], list)
    assert len(data["operations"]) > 0
    first = data["operations"][0]
    assert "name" in first
    assert "compute_weight" in first


def test_ops_threshold_filter():
    runner = CliRunner()
    result_high = runner.invoke(cli, ["ops", "--threshold", "high"])
    result_all = runner.invoke(cli, ["ops", "--threshold", "low"])
    high_data = json.loads(result_high.output)
    all_data = json.loads(result_all.output)
    assert len(all_data["operations"]) >= len(high_data["operations"])
