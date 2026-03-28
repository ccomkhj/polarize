"""Pandas: groupby inside a loop (high compute weight due to loop context)."""
import sys
import pandas as pd


def main(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    results = []
    for region in df["region"].unique():
        subset = df[df["region"] == region]
        agg = subset.groupby("month").agg({"revenue": "sum"}).reset_index()
        agg["region"] = region
        results.append(agg)
    result = pd.concat(results).sort_values(["region", "month"]).reset_index(drop=True)
    return result


if __name__ == "__main__":
    out = main(sys.argv[1])
    out.to_csv(sys.stdout, index=False)
