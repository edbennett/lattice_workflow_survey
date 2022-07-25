import numpy as np
import pandas as pd
import pytest

from limesurvey_parser import LimeSurveyParser


@pytest.fixture
def parser() -> LimeSurveyParser:
    return LimeSurveyParser()


def test_returns_data_frame_on_empty_input(parser: LimeSurveyParser) -> None:
    assert type(parser.parse("")) == pd.DataFrame


def test_parses_first_line_as_header(parser: LimeSurveyParser) -> None:
    assert parser.parse("header").columns == pd.Index(["header"])


def test_parses_second_line_as_data(parser: LimeSurveyParser) -> None:
    assert parser.parse("header\ndata").values == np.array(["data"])


def test_uses_semicolon_as_default_separator(parser: LimeSurveyParser) -> None:
    assert (
        (
            parser.parse("header1;header2\ndata1;data2")
            == pd.DataFrame([["data1", "data2"]], columns=["header1", "header2"])
        )
        # a bit weird but first creates a pd.Series, second makes a bool:
        .all().all()
    )


def test_separator_can_be_configured() -> None:
    parser = LimeSurveyParser(sep=",")
    assert (
        (
            parser.parse("header1,header2\ndata1,data2")
            == pd.DataFrame([["data1", "data2"]], columns=["header1", "header2"])
        )
        # a bit weird but first creates a pd.Series, second makes a bool:
        .all().all()
    )


def test_parses_question_id(parser: LimeSurveyParser) -> None:
    assert parser.parse_question_id("G01Q02") == dict(group=1, question=2)
