from io import StringIO
from typing import Dict

import pandas as pd
import parse


class LimeSurveyParser:
    sep: str

    def __init__(self, sep: str = ";") -> None:
        self.sep = sep

    def parse(self, content: str) -> pd.DataFrame:
        if not content:
            return pd.DataFrame()
        return pd.read_csv(StringIO(content), header=0, sep=self.sep)

    def parse_question_id(self, heading: str) -> Dict[str, int]:
        # The extra `dict` is a dirty hack for mypy. Should better use a stub
        # file here probably.
        return dict(parse.parse("G{group:d}Q{question:d}", heading).named)
