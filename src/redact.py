from argparse import ArgumentParser
import sys

import pandas as pd


def redact(df, question_ids):
    for column in df.columns:
        for question_id in question_ids:
            if question_id in column and column in df.columns:
                df = df.drop(columns=column)
    return df


def main():
    parser = ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("question_ids", nargs="+")
    parser.add_argument("--output_filename", default=sys.stdout)
    parser.add_argument("--delimiter", default=";")
    args = parser.parse_args()

    df = redact(
        pd.read_csv(args.input_filename, delimiter=args.delimiter),
        args.question_ids
    )
    df.to_csv(args.output_filename, sep=args.delimiter)


if __name__ == "__main__":
    main()
