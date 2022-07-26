from io import StringIO
from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd
import parse


class LimeSurveyParser:
    sep_csv: str
    sep_header: str

    def __init__(self, sep_csv: str = ";", sep_header: str = "---") -> None:
        self.sep_csv = sep_csv
        self.sep_header = sep_header

    def parse(self, content: str) -> pd.DataFrame:
        if not content:
            return pd.DataFrame()
        original_data = pd.read_csv(
            StringIO(content), header=0, index_col=0, sep=self.sep_csv
        )
        return self._organize_header(original_data)

    def is_question_id(self, header_entry: str) -> bool:
        return self.parse_question_id(header_entry) is not None

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

    def parse_question_id(self, id_string: str) -> Optional[Dict[str, int]]:
        for extracted_ids in [
            parse.parse("G{group:d}Q{question:d}", id_string),
            parse.parse("G{group:d}Q{question:d}[SQ{answer:d}]", id_string),
        ]:
            if extracted_ids is not None:
                # The extra `dict` is a dirty hack for mypy. Should better use a stub
                # file here probably.
                return dict(extracted_ids.named)
        return None

    def parse_metadata(self, content: str) -> pd.DataFrame:
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
            (lambda ids: [ids["group"], ids["question"], ids["answer"]])(
                self.parse_question_id(id_string)
            )
            for id_string in columns["id"]
        ]
        question_data.columns = pd.MultiIndex.from_frame(
            columns[["id", "group_id", "question_id", "answer_id", "title", "answer"]]
        )
        return question_data
