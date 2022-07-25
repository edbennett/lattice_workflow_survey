from io import StringIO
from typing import Dict, Iterable, Optional

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
        original_data = pd.read_csv(StringIO(content), header=0, sep=self.sep_csv)
        return self._organize_header(original_data)

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

    def parse_question_id(self, id_string: str) -> Dict[str, int]:
        # The extra `dict` is a dirty hack for mypy. Should better use a stub
        # file here probably.
        id = parse.parse("G{group:d}Q{question:d}", id_string)
        if id is not None:
            # Parsing was sucessful, so no additional answer id is present.
            return dict(id.named)
        return dict(
            parse.parse("G{group:d}Q{question:d}[SQ{answer:d}]", id_string).named
        )
