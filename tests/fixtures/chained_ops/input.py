"""Pandas: chained filter + groupby + sort."""
import sys
import pandas as pd


def main(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    result = (
        df[df["status"] == "success"]
        .groupby("user_id")
        .agg({"duration": "mean"})
        .reset_index()
        .sort_values("duration", ascending=False)
        .reset_index(drop=True)
    )
    return result


if __name__ == "__main__":
    out = main(sys.argv[1])
    out.to_csv(sys.stdout, index=False)
