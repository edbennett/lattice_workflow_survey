import pandas as pd
from io import StringIO


class LimeSurveyParser:
    def __init__(self) -> None:
        pass

    def parse(self, content: str) -> pd.DataFrame:
        if not content:
            return pd.DataFrame()
        return pd.read_csv(StringIO(content), header=0, sep=";")
