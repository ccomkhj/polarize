"""Polars: groupby + agg on sales data."""
import sys
import polars as pl


def main(data_path: str) -> pl.DataFrame:
    df = pl.read_csv(data_path)
    result = df.group_by("user_id").agg(pl.col("amount").sum())
    result = result.sort("user_id")
    return result


if __name__ == "__main__":
    out = main(sys.argv[1])
    out.write_csv(sys.stdout)
