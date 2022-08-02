import sys
from argparse import ArgumentParser
from typing import List

import pandas as pd


def redact(df: pd.DataFrame, question_ids: List[str]) -> pd.DataFrame:
    for column in df.columns:
        for question_id in question_ids:
            if question_id in column and column in df.columns:
                df = df.drop(columns=column)
    return df


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("question_ids", nargs="+")
    parser.add_argument("--output_filename", default=sys.stdout)
    parser.add_argument("--delimiter", default=";")
    args = parser.parse_args()

    df = redact(
        pd.read_csv(args.input_filename, delimiter=args.delimiter), args.question_ids
    )
    df.to_csv(args.output_filename, sep=args.delimiter)


if __name__ == "__main__":
    main()
