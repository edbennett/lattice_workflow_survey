#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from io import StringIO
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import parse


class LimeSurveyParser:
    """
    Parse LimeSurvey's exported csv files.

    This parser parses LimeSurvey's csv files into `pd.DataFrame`s. It is
    basically a convenience wrapper around `pd.read_csv()`. It assumes that you
    have exported your survey responses under `Responses > Export > Export
    responses` with `Headings` set to "Queston code & question text" and a
    reasonable "Code/text separator" into csv format. All methods get their
    data as strings, i.e. it is in the users responsibility to read the file
    into a python string.

    Attributes
    ----------
    sep_csv : str
        The csv separator, i.e. separator between columns.
        Default: ";"
    sep_header : str
        The separator between ID and title in the header, i.e. what is set under
        `Headings > Code/text separator` on the `Export` website.
        Default: "---"

    Methods
    -------
    parse(content: str) -> pd.DataFrame:
        Very simple parsing, mostly meant for internal purposes. Returns the
        full data set with `id---Response ID` as index and a header with two rows
        `id` and `title`.
    parse_metadata(content: str) -> pd.DataFrame:
        Same as parse, but strips away everything related to the actual
        questions, i.e. only keeps start date, seed, etc. and converts the dates
        to timestamps.
    parse_questions(content: str) -> pd.DataFrame:
        Only keeps questions and their answers while discarding metadata and
        timing information. Builds a convenient header by splitting the IDs for
        the questions into group_id, question_id and (if applicable) answer_id
        such that
        ```
        LimeSurveyParser().parse_questions(content).T.query("question_id=10")
        ```
        returns all data for question 10. Please note the extra transposition
        because `pandas` seems to struggle with `query`ing a column MultiIndex.

    """

    sep_csv: str
    sep_header: str

    def __init__(self, sep_csv: str = ";", sep_header: str = "---") -> None:
        self.sep_csv = sep_csv
        self.sep_header = sep_header

    def parse(self, content: str) -> pd.DataFrame:
        """Parse into simple structure for internal purposes."""
        if not content:
            return pd.DataFrame()
        original_data = pd.read_csv(
            StringIO(content), header=0, index_col=0, sep=self.sep_csv
        )
        return self._organize_header(original_data)

    def is_question_id(self, header_entry: str) -> bool:
        """Find out if this id belongs to a question or not."""
        return bool(self.parse_question_id(header_entry))

    def _organize_header(self, data: pd.DataFrame) -> pd.DataFrame:
        data.columns = pd.MultiIndex.from_tuples(
            self._insert_default_id(
                entry.split(self.sep_header) for entry in data.columns
            ),
            names=["id", "title"],
        )
        return data

    def _insert_default_id(
        self, columns: Iterable[tuple[str, ...]]
    ) -> list[tuple[Optional[str], ...]]:
        return [tup if len(tup) == 2 else (None, tup[0]) for tup in columns]

    def parse_question_id(self, id_string: str) -> dict[str, int]:
        """Split the question_id of the form `G01Q02[SQ003]`."""
        # The extra `dict` is a dirty hack for mypy. Should better use a stub
        # file here probably.
        return dict(
            (
                parse.parse("G{group:d}Q{question:d}", id_string)
                or parse.parse("G{group:d}Q{question:d}[SQ{answer:d}]", id_string)
                or parse.Result(None, dict[str, int](), None)
            ).named
        )

    def parse_metadata(self, content: str) -> pd.DataFrame:
        """Strip questions and return only parsed metadata."""
        return self._convert_pertinent_columns_to_timestamps(
            self._select_columns_before_first_question(self.parse(content))
        )

    def _select_columns_before_first_question(
        self, full_data: pd.DataFrame
    ) -> pd.DataFrame:
        return full_data.iloc[
            :,
            np.cumprod(
                [
                    not self.is_question_id(identifier)
                    for identifier in full_data.columns.get_level_values("id")
                ],
                dtype=bool,
            ),
        ].copy()

    def _convert_pertinent_columns_to_timestamps(
        self, metadata: pd.DataFrame
    ) -> pd.DataFrame:
        for key in metadata.columns:
            if "date" in key[0] and "Date" in key[1]:
                metadata[key] = pd.to_datetime(
                    metadata[key], format="%Y-%m-%d %H:%M:%S"
                )
        return metadata

    def parse_questions(self, content: str) -> pd.DataFrame:
        """Parse the main bulk of the data related to the actual questions."""
        return self._add_partial_ids_to_header(
            self._add_header_row_with_answer(
                self._select_questions(self.parse(content))
            )
        )

    def _select_questions(self, full_data: pd.DataFrame) -> pd.DataFrame:
        return full_data.iloc[
            :,
            [
                self.is_question_id(id_string)
                for id_string in full_data.columns.get_level_values("id")
            ],
        ]

    def _add_header_row_with_answer(self, question_data: pd.DataFrame) -> pd.DataFrame:
        columns = question_data.columns.to_frame()
        columns[["title", "answer"]] = [
            self._split_into_title_and_answer(title) for title in columns["title"]
        ]
        question_data.columns = pd.MultiIndex.from_frame(columns)
        return question_data

    def _split_into_title_and_answer(self, title: str) -> tuple[str, Optional[str]]:
        return (
            lambda parsed: (parsed["title"], parsed["answer"])
            if parsed is not None
            else (title, None)
        )(parse.parse("{title} [{answer}]", title))

    def _add_partial_ids_to_header(self, question_data: pd.DataFrame) -> pd.DataFrame:
        columns = question_data.columns.to_frame()
        columns[["group_id", "question_id", "answer_id"]] = [
            (
                lambda ids: [
                    ids["group"],
                    ids["question"],
                    ids["answer"] if "answer" in ids else None,
                ]
            )(self.parse_question_id(id_string))
            for id_string in columns["id"]
        ]
        question_data.columns = pd.MultiIndex.from_frame(
            columns[["id", "group_id", "question_id", "answer_id", "title", "answer"]]
        )
        return question_data
