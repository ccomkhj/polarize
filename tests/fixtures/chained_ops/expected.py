"""Polars: chained filter + groupby + sort."""
import sys
import polars as pl


def main(data_path: str) -> pl.DataFrame:
    df = pl.read_csv(data_path)
    result = (
        df.filter(pl.col("status") == "success")
        .group_by("user_id")
        .agg(pl.col("duration").mean())
        .sort("duration", descending=True)
    )
    return result


if __name__ == "__main__":
    out = main(sys.argv[1])
    out.write_csv(sys.stdout)
