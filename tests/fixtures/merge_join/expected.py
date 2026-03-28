"""Polars: merge orders with customers."""
import sys
import polars as pl


def main(orders_path: str, customers_path: str) -> pl.DataFrame:
    orders = pl.read_csv(orders_path)
    customers = pl.read_csv(customers_path)
    result = orders.join(customers, on="customer_id", how="left")
    result = result.sort("order_id")
    return result


if __name__ == "__main__":
    out = main(sys.argv[1], sys.argv[2])
    out.write_csv(sys.stdout)
