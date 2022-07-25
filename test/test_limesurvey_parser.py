import pytest
from limesurvey_parser import LimeSurveyParser
import pandas as pd


@pytest.fixture
def parser() -> LimeSurveyParser:
    return LimeSurveyParser()


def test_returns_data_frame_on_empty_input(parser) -> None:
    assert type(parser.parse("")) == pd.DataFrame


def test_parses_first_line_as_header(parser) -> None:
    assert parser.parse("header").columns == pd.Index(["header"])
