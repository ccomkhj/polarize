"""E2E tests: full discover → validate → profile pipeline via CLI."""
import json

from click.testing import CliRunner

from polarize.cli import cli


def test_full_pipeline_groupby_agg(groupby_agg_dir):
    runner = CliRunner()
    input_file = str(groupby_agg_dir / "input.py")
    expected_file = str(groupby_agg_dir / "expected.py")
    data_path = str(groupby_agg_dir / "data" / "sales.csv")

    # Step 1: Discover
    discover_result = runner.invoke(cli, ["discover", input_file, "--threshold", "high"])
    assert discover_result.exit_code == 0
    report = json.loads(discover_result.output)
    assert report["summary"]["compute_heavy_ops"] > 0

    # Step 2: (Agent would convert here — we use the expected fixture)

    # Step 3: Validate
    validate_result = runner.invoke(cli, [
        "validate", "--original", input_file, "--converted", expected_file,
        "--", data_path,
    ])
    assert validate_result.exit_code == 0
    validation = json.loads(validate_result.output)
    assert validation["status"] == "pass"

    # Step 4: Profile
    profile_result = runner.invoke(cli, [
        "profile", "--original", input_file, "--converted", expected_file,
        "--runs", "2", "--", data_path,
    ])
    assert profile_result.exit_code == 0
    bench = json.loads(profile_result.output)
    assert bench["original_time_s"] > 0
    assert bench["converted_time_s"] > 0
    assert bench["runs"] == 2


def test_full_pipeline_merge_join(merge_join_dir):
    runner = CliRunner()
    input_file = str(merge_join_dir / "input.py")
    expected_file = str(merge_join_dir / "expected.py")
    orders = str(merge_join_dir / "data" / "orders.csv")
    customers = str(merge_join_dir / "data" / "customers.csv")

    # Discover
    discover_result = runner.invoke(cli, ["discover", input_file])
    assert discover_result.exit_code == 0

    # Validate with multiple args
    validate_result = runner.invoke(cli, [
        "validate", "--original", input_file, "--converted", expected_file,
        "--", orders, customers,
    ])
    assert validate_result.exit_code == 0
    validation = json.loads(validate_result.output)
    assert validation["status"] == "pass"

    # Profile with multiple args
    profile_result = runner.invoke(cli, [
        "profile", "--original", input_file, "--converted", expected_file,
        "--runs", "2", "--", orders, customers,
    ])
    assert profile_result.exit_code == 0


def test_full_pipeline_chained_ops(chained_ops_dir):
    runner = CliRunner()
    input_file = str(chained_ops_dir / "input.py")
    expected_file = str(chained_ops_dir / "expected.py")
    data_path = str(chained_ops_dir / "data" / "logs.csv")

    # Discover — should find multiple ops
    discover_result = runner.invoke(cli, ["discover", input_file, "--threshold", "low"])
    assert discover_result.exit_code == 0
    report = json.loads(discover_result.output)
    assert len(report["operations"]) >= 2

    # Validate
    validate_result = runner.invoke(cli, [
        "validate", "--original", input_file, "--converted", expected_file,
        "--", data_path,
    ])
    assert validate_result.exit_code == 0
    validation = json.loads(validate_result.output)
    assert validation["status"] == "pass"
