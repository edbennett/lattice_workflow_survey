from typing import Iterable

import numpy as np
import pandas as pd
import pytest

from limesurvey_parser import LimeSurveyParser


@pytest.fixture
def parser() -> LimeSurveyParser:
    return LimeSurveyParser()


@pytest.fixture
def metadata() -> str:
    return '''"id---Response ID";"submitdate---Date submitted";"G01Q01[SQ001]---Question?"\n
1;2022-01-01 00:00:00;"Yes"'''


@pytest.fixture
def parsed_metadata() -> pd.DataFrame:
    return pd.DataFrame(
        [["2022-01-01 00:00:00"]],
        index=pd.Index([1], name="id---Response ID"),
        columns=pd.MultiIndex.from_tuples(
            [("submitdate", "Date submitted")], names=["id", "title"]
        ),
    )


def make_columns_structure_from(titles: Iterable[str]) -> pd.MultiIndex:
    return pd.MultiIndex.from_tuples(
        [(None, title) for title in titles], names=["id", "title"]
    )


def test_returns_data_frame_on_empty_input(parser: LimeSurveyParser) -> None:
    assert type(parser.parse("")) == pd.DataFrame


def test_parses_first_line_as_header(parser: LimeSurveyParser) -> None:
    assert parser.parse("index;header").columns == make_columns_structure_from(
        ["header"]
    )


def test_parses_second_line_as_data(parser: LimeSurveyParser) -> None:
    assert parser.parse("index;header\nindex;data").values == np.array(["data"])


def test_uses_semicolon_as_default_separator(parser: LimeSurveyParser) -> None:
    assert (
        (
            parser.parse("header1;header2\ndata1;data2")
            == pd.DataFrame(
                [["data2"]],
                index=pd.Index(["data1"], name="header1"),
                columns=make_columns_structure_from(["header2"]),
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
                [["data2"]],
                index=pd.Index(["data1"], name="header1"),
                columns=make_columns_structure_from(["header2"]),
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
        "index;head_id" + default_separator + "head_title"
    ).columns == pd.MultiIndex.from_tuples(
        [("head_id", "head_title")], names=["id", "title"]
    )


def test_for_confidence_splits_headers_with_multiple_entries(
    parser: LimeSurveyParser,
) -> None:
    assert (
        (
            parser.parse("index;1---first;2---second").columns
            == pd.MultiIndex.from_tuples(
                [("1", "first"), ("2", "second")], names=["id", "title"]
            )
        )
        # a bit weird but first creates a pd.Series, second makes a bool:
        .all().all()
    )


def test_recognizes_question_id(parser: LimeSurveyParser) -> None:
    assert parser.is_question_id("G01Q02")


def test_recognizes_question_ids_with_selection(parser: LimeSurveyParser) -> None:
    assert parser.is_question_id("G01Q02[SQ003]")


def test_recognizes_non_question_ids(parser: LimeSurveyParser) -> None:
    assert not parser.is_question_id("id")


def test_uses_first_column_as_index(parser: LimeSurveyParser) -> None:
    assert parser.parse("index;header\nindex entry;data").index == pd.Index(
        ["index entry"]
    )


def test_parses_all_before_first_question_as_metadata(
    parser: LimeSurveyParser, metadata: str, parsed_metadata: pd.DataFrame
) -> None:
    assert (parser.parse_metadata(metadata) == parsed_metadata).all().all()


def test_parses_dates_in_metadata_as_datetime(
    parser: LimeSurveyParser, metadata: str
) -> None:
    assert type(parser.parse_metadata(metadata).iloc[0, 0]) == pd.Timestamp
