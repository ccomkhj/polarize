"""Polars: groupby without loop — single expression."""
import sys
import polars as pl


def main(data_path: str) -> pl.DataFrame:
    df = pl.read_csv(data_path)
    result = (
        df.group_by(["region", "month"])
        .agg(pl.col("revenue").sum())
        .sort(["region", "month"])
    )
    return result


if __name__ == "__main__":
    out = main(sys.argv[1])
    out.write_csv(sys.stdout)
