"""Pandas: groupby + agg on sales data."""
import sys
import pandas as pd


def main(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    result = df.groupby("user_id").agg({"amount": "sum"}).reset_index()
    result = result.sort_values("user_id").reset_index(drop=True)
    return result


if __name__ == "__main__":
    out = main(sys.argv[1])
    out.to_csv(sys.stdout, index=False)
