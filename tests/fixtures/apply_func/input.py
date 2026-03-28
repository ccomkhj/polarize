"""Pandas: apply function to compute total with tax."""
import sys
import pandas as pd


def main(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    df["total"] = df.apply(lambda row: row["amount"] * (1 + row["tax_rate"]), axis=1)
    result = df.sort_values("id").reset_index(drop=True)
    return result


if __name__ == "__main__":
    out = main(sys.argv[1])
    out.to_csv(sys.stdout, index=False)
