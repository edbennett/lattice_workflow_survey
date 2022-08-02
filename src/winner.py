#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from typing import List, TextIO, Union

import numpy as np
import pandas as pd

from limesurvey_parser import LimeSurveyParser


def get_responses(results_file: TextIO, sep_header: str = "%%%") -> pd.DataFrame:
    parser = LimeSurveyParser(sep_header=sep_header)
    content = results_file.read()
    return parser.parse_questions(content)


def get_winners(
    responses: pd.DataFrame,
    num_winners: int = 1,
    optin_question: int = 0,
    id_question: int = 1,
    seed: Union[int, None] = None,
) -> List[str]:
    rng = np.random.default_rng(seed=seed)
    eligible_df = responses.T.query(f"question_id=={optin_question}").T == "Yes"
    eligible_idx = eligible_df[eligible_df.columns[0]]
    candidates = (
        responses.T.query(f"question_id=={id_question}").T[eligible_idx].values[:, 0]
    )
    if candidates.size <= num_winners:
        return sorted(candidates)
    return sorted(rng.choice(candidates, size=num_winners, replace=False))


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("unredacted_results", type=FileType("r"))
    parser.add_argument("--seed", default=None, type=int)
    parser.add_argument("--num_winners", default=1, type=int)
    parser.add_argument("--optin_question", default=0, type=int)
    parser.add_argument("--id_question", default=1, type=int)
    parser.add_argument("--sep_header", default="%%%")
    args = parser.parse_args()

    responses = get_responses(args.unredacted_results, args.sep_header)
    print(
        "\n".join(
            get_winners(
                responses,
                args.num_winners,
                args.optin_question,
                args.id_question,
                args.seed,
            )
        )
    )


if __name__ == "__main__":
    main()
