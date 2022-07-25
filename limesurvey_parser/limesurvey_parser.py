import pandas as pd
from io import StringIO


class LimeSurveyParser:
    sep: str

    def __init__(self, sep: str = ";") -> None:
        self.sep = sep

    def parse(self, content: str) -> pd.DataFrame:
        if not content:
            return pd.DataFrame()
        return pd.read_csv(StringIO(content), header=0, sep=self.sep)
