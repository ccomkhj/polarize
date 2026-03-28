"""Pandas: sort_values on events."""
import sys
import pandas as pd


def main(data_path: str) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    result = df.sort_values("timestamp").reset_index(drop=True)
    return result


if __name__ == "__main__":
    out = main(sys.argv[1])
    out.to_csv(sys.stdout, index=False)
