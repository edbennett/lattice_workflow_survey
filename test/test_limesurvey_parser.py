from limesurvey_parser import LimeSurveyParser
import pandas as pd


def test_returns_data_frame_on_empty_input() -> None:
    parser = LimeSurveyParser()
    assert type(parser.parse("")) == pd.DataFrame


def test_parses_first_line_as_header() -> None:
    parser = LimeSurveyParser()
    assert parser.parse("header").columns == pd.Index(["header"])
