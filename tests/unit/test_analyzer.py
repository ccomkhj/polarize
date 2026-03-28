"""Tests for AST-based pandas operation detection."""
import textwrap

from polarize.discovery.analyzer import analyze_source


def test_detects_import_pandas():
    source = textwrap.dedent("""\
        import pandas as pd
        df = pd.read_csv("data.csv")
    """)
    result = analyze_source(source)
    assert result.pandas_alias == "pd"


def test_detects_import_pandas_custom_alias():
    source = textwrap.dedent("""\
        import pandas as panda
        df = panda.read_csv("data.csv")
    """)
    result = analyze_source(source)
    assert result.pandas_alias == "panda"


def test_detects_no_pandas():
    source = textwrap.dedent("""\
        import json
        data = json.loads('{}')
    """)
    result = analyze_source(source)
    assert result.pandas_alias is None
    assert result.operations == []


def test_detects_groupby():
    source = textwrap.dedent("""\
        import pandas as pd
        df = pd.read_csv("data.csv")
        result = df.groupby("col").sum()
    """)
    result = analyze_source(source)
    ops = [op for op in result.operations if op.operation == "groupby"]
    assert len(ops) == 1
    assert ops[0].line == 3


def test_detects_merge():
    source = textwrap.dedent("""\
        import pandas as pd
        df1 = pd.read_csv("a.csv")
        df2 = pd.read_csv("b.csv")
        merged = df1.merge(df2, on="id")
    """)
    result = analyze_source(source)
    ops = [op for op in result.operations if op.operation == "merge"]
    assert len(ops) == 1
    assert ops[0].line == 4


def test_detects_sort_values():
    source = textwrap.dedent("""\
        import pandas as pd
        df = pd.read_csv("data.csv")
        df = df.sort_values("col")
    """)
    result = analyze_source(source)
    ops = [op for op in result.operations if op.operation == "sort_values"]
    assert len(ops) == 1


def test_detects_apply():
    source = textwrap.dedent("""\
        import pandas as pd
        df = pd.read_csv("data.csv")
        df["new"] = df.apply(lambda row: row["a"] + row["b"], axis=1)
    """)
    result = analyze_source(source)
    ops = [op for op in result.operations if op.operation == "apply"]
    assert len(ops) == 1


def test_detects_read_calls():
    source = textwrap.dedent("""\
        import pandas as pd
        df1 = pd.read_csv("a.csv")
        df2 = pd.read_parquet("b.parquet")
        df3 = pd.read_json("c.json")
    """)
    result = analyze_source(source)
    assert len(result.read_calls) == 3
    assert result.read_calls[0].method == "read_csv"
    assert result.read_calls[1].method == "read_parquet"
    assert result.read_calls[2].method == "read_json"


def test_detects_chained_operations():
    source = textwrap.dedent("""\
        import pandas as pd
        df = pd.read_csv("data.csv")
        result = df.groupby("a").agg({"b": "sum"}).sort_values("b")
    """)
    result = analyze_source(source)
    ops = result.operations
    op_names = [op.operation for op in ops]
    assert "groupby" in op_names
    assert "sort_values" in op_names


def test_detects_operation_inside_loop():
    source = textwrap.dedent("""\
        import pandas as pd
        df = pd.read_csv("data.csv")
        for region in df["region"].unique():
            subset = df[df["region"] == region]
            agg = subset.groupby("month").sum()
    """)
    result = analyze_source(source)
    ops = [op for op in result.operations if op.operation == "groupby"]
    assert len(ops) == 1
    assert ops[0].in_loop is True


def test_captures_source_code_snippet():
    source = textwrap.dedent("""\
        import pandas as pd
        df = pd.read_csv("data.csv")
        result = df.groupby("user_id").agg({"amount": "sum"})
    """)
    result = analyze_source(source)
    ops = [op for op in result.operations if op.operation == "groupby"]
    assert "groupby" in ops[0].code
