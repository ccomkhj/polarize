"""Polars: compute total with tax using expressions."""
import sys
import polars as pl


def main(data_path: str) -> pl.DataFrame:
    df = pl.read_csv(data_path)
    df = df.with_columns(
        (pl.col("amount") * (1 + pl.col("tax_rate"))).alias("total")
    )
    result = df.sort("id")
    return result


if __name__ == "__main__":
    out = main(sys.argv[1])
    out.write_csv(sys.stdout)
