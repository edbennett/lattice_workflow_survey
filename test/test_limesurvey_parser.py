from typing import Iterable

import numpy as np
import pandas as pd
import pytest

from limesurvey_parser import LimeSurveyParser


@pytest.fixture
def parser() -> LimeSurveyParser:
    return LimeSurveyParser()


def make_columns_structure_from(titles: Iterable[str]) -> pd.MultiIndex:
    return pd.MultiIndex.from_tuples(
        [(None, title) for title in titles], names=["id", "title"]
    )


def test_returns_data_frame_on_empty_input(parser: LimeSurveyParser) -> None:
    assert type(parser.parse("")) == pd.DataFrame


def test_parses_first_line_as_header(parser: LimeSurveyParser) -> None:
    assert parser.parse("header").columns == make_columns_structure_from(["header"])


def test_parses_second_line_as_data(parser: LimeSurveyParser) -> None:
    assert parser.parse("header\ndata").values == np.array(["data"])


def test_uses_semicolon_as_default_separator(parser: LimeSurveyParser) -> None:
    assert (
        (
            parser.parse("header1;header2\ndata1;data2")
            == pd.DataFrame(
                [["data1", "data2"]],
                columns=make_columns_structure_from(["header1", "header2"]),
            )
        )
        # a bit weird but first creates a pd.Series, second makes a bool:
        .all().all()
    )


def test_separator_can_be_configured() -> None:
    parser = LimeSurveyParser(sep_csv=",")
    assert (
        (
            parser.parse("header1,header2\ndata1,data2")
            == pd.DataFrame(
                [["data1", "data2"]],
                columns=make_columns_structure_from(["header1", "header2"]),
            )
        )
        # a bit weird but first creates a pd.Series, second makes a bool:
        .all().all()
    )


def test_parses_question_id(parser: LimeSurveyParser) -> None:
    assert parser.parse_question_id("G01Q02") == dict(group=1, question=2)


def test_parses_question_id_with_selected_answer(parser: LimeSurveyParser) -> None:
    assert parser.parse_question_id("G01Q2[SQ003]") == dict(
        group=1, question=2, answer=3
    )


def test_splits_headers_with_separator_in_them(parser: LimeSurveyParser) -> None:
    default_separator = "---"
    assert parser.parse(
        "head_id" + default_separator + "head_title"
    ).columns == pd.MultiIndex.from_tuples(
        [("head_id", "head_title")], names=["id", "title"]
    )


def test_for_confidence_splits_headers_with_multiple_entries(
    parser: LimeSurveyParser,
) -> None:
    assert (
        (
            parser.parse("1---first;2---second").columns
            == pd.MultiIndex.from_tuples(
                [("1", "first"), ("2", "second")], names=["id", "title"]
            )
        )
        # a bit weird but first creates a pd.Series, second makes a bool:
        .all().all()
    )
