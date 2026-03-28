"""Pandas: merge orders with customers."""
import sys
import pandas as pd


def main(orders_path: str, customers_path: str) -> pd.DataFrame:
    orders = pd.read_csv(orders_path)
    customers = pd.read_csv(customers_path)
    result = orders.merge(customers, on="customer_id", how="left")
    result = result.sort_values("order_id").reset_index(drop=True)
    return result


if __name__ == "__main__":
    out = main(sys.argv[1], sys.argv[2])
    out.to_csv(sys.stdout, index=False)
