"""Integration tests: discovery analyzer + scorer + reporter end-to-end."""
from polarize import discover


def test_groupby_agg_discovery(groupby_agg_dir):
    report = discover(str(groupby_agg_dir / "input.py"), threshold="low")
    assert report["file"].endswith("input.py")
    assert report["summary"]["total_ops"] > 0
    op_names = [op["operation"] for op in report["operations"]]
    assert "groupby" in op_names
    assert len(report["data_sources"]) >= 1
    assert report["data_sources"][0]["method"] == "read_csv"


def test_merge_join_discovery(merge_join_dir):
    report = discover(str(merge_join_dir / "input.py"), threshold="low")
    op_names = [op["operation"] for op in report["operations"]]
    assert "merge" in op_names
    assert len(report["data_sources"]) == 2


def test_chained_ops_discovery(chained_ops_dir):
    report = discover(str(chained_ops_dir / "input.py"), threshold="low")
    op_names = [op["operation"] for op in report["operations"]]
    assert "groupby" in op_names
    assert "sort_values" in op_names


def test_loop_groupby_discovery(loop_groupby_dir):
    report = discover(str(loop_groupby_dir / "input.py"), threshold="low")
    loop_ops = [op for op in report["operations"] if "context" in op and "loop" in op["context"]]
    assert len(loop_ops) >= 1


def test_threshold_high_filters_correctly(groupby_agg_dir):
    report_high = discover(str(groupby_agg_dir / "input.py"), threshold="high")
    report_low = discover(str(groupby_agg_dir / "input.py"), threshold="low")
    for op in report_high["operations"]:
        assert op["compute_weight"] == "high"
    assert len(report_low["operations"]) >= len(report_high["operations"])


def test_conversion_order_is_by_impact(chained_ops_dir):
    report = discover(str(chained_ops_dir / "input.py"), threshold="low")
    ops = report["operations"]
    weights = {"high": 3, "medium": 2, "low": 1}
    op_weights = [weights[op["compute_weight"]] for op in ops]
    assert op_weights == sorted(op_weights, reverse=True)
