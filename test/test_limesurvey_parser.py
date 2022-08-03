#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Iterable

import numpy as np
import pandas as pd
import pytest

from limesurvey_parser import LimeSurveyParser


@pytest.fixture
def parser() -> LimeSurveyParser:
    return LimeSurveyParser()


@pytest.fixture
def realistic_data() -> str:
    return '''"id---Response ID";"submitdate---Date submitted";"G01Q02[SQ003]---Question? [Answer]";"G02Q42---Another question?"
1;2022-01-01 00:00:00;"Yes";"No"'''


@pytest.fixture
def parsed_metadata() -> pd.DataFrame:
    return pd.DataFrame(
        [[pd.to_datetime("2022-01-01 00:00:00")]],
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
    assert parser.parse("header1;header2\ndata1;data2").equals(
        pd.DataFrame(
            [["data2"]],
            index=pd.Index(["data1"], name="header1"),
            columns=make_columns_structure_from(["header2"]),
        )
    )


def test_separator_can_be_configured() -> None:
    parser = LimeSurveyParser(sep_csv=",")
    assert parser.parse("header1,header2\ndata1,data2").equals(
        pd.DataFrame(
            [["data2"]],
            index=pd.Index(["data1"], name="header1"),
            columns=make_columns_structure_from(["header2"]),
        )
    )


def test_parses_question_id(parser: LimeSurveyParser) -> None:
    assert parser.parse_question_id("G01Q02") == dict(group=1, question=2)


def test_parses_question_id_with_selected_answer(parser: LimeSurveyParser) -> None:
    assert parser.parse_question_id("G01Q2[SQ003]") == dict(
        group=1, question=2, answer=3
    )


def test_parses_question_id_with_other_answer(parser: LimeSurveyParser) -> None:
    assert parser.parse_question_id("G01Q2[other]") == dict(
        group=1, question=2, answer="other"
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
    assert parser.parse("index;1---first;2---second").columns.equals(
        pd.MultiIndex.from_tuples(
            [("1", "first"), ("2", "second")], names=["id", "title"]
        )
    )


def test_recognizes_question_id(parser: LimeSurveyParser) -> None:
    assert parser.is_question_id("G01Q02")


def test_recognizes_question_ids_with_selection(parser: LimeSurveyParser) -> None:
    assert parser.is_question_id("G01Q02[SQ003]")


def test_recognizes_question_ids_with_other(parser: LimeSurveyParser) -> None:
    assert parser.is_question_id("G01Q02[other]")


def test_recognizes_non_question_ids(parser: LimeSurveyParser) -> None:
    assert not parser.is_question_id("id")


def test_uses_first_column_as_index(parser: LimeSurveyParser) -> None:
    assert parser.parse("index;header\nindex entry;data").index == pd.Index(
        ["index entry"]
    )


def test_parses_all_before_first_question_as_metadata(
    parser: LimeSurveyParser, realistic_data: str, parsed_metadata: pd.DataFrame
) -> None:
    assert parser.parse_metadata(realistic_data).equals(parsed_metadata)


def test_parses_dates_in_metadata_as_datetime(
    parser: LimeSurveyParser, realistic_data: str
) -> None:
    assert type(parser.parse_metadata(realistic_data).iloc[0, 0]) == pd.Timestamp


def test_does_not_convert_dates_if_only_id_contains_date(
    parser: LimeSurveyParser, realistic_data: str
) -> None:
    realistic_data = realistic_data.replace("Date", "Fate")
    assert type(parser.parse_metadata(realistic_data).iloc[0, 0]) != pd.Timestamp


def test_does_not_convert_dates_if_only_title_contains_date(
    parser: LimeSurveyParser, realistic_data: str
) -> None:
    realistic_data = realistic_data.replace("date", "fate")
    assert type(parser.parse_metadata(realistic_data).iloc[0, 0]) != pd.Timestamp


def test_parsing_questions_with_selection_splits_title(
    parser: LimeSurveyParser, realistic_data: str
) -> None:
    assert (
        lambda parsed, expected: (
            np.logical_or(
                np.logical_and(pd.isna(parsed).values, pd.isna(expected)),
                parsed.values == expected,
            )
        ).all()
    )(
        parser.parse_questions(realistic_data).columns.to_frame()[["title", "answer"]],
        [["Question?", "Answer"], ["Another question?", np.nan]],
    )


def test_parsing_questions_without_selection_has_nan_as_answer(
    parser: LimeSurveyParser, realistic_data: str
) -> None:
    assert np.isnan(
        parser.parse_questions(realistic_data)
        .columns.to_frame()[["title", "answer"]]
        .values[-1, -1]
    )


def test_selects_only_questions_when_parsing_questions(
    parser: LimeSurveyParser, realistic_data: str
) -> None:
    assert all(
        parser.is_question_id(id_string)
        for id_string in parser.parse_questions(
            realistic_data
        ).columns.get_level_values("id")
    )


def test_adds_finegrained_information_to_questions_header(
    parser: LimeSurveyParser, realistic_data: str
) -> None:
    assert parser.parse_questions(realistic_data).columns.names == [
        "id",
        "group_id",
        "question_id",
        "answer_id",
        "title",
        "answer",
    ]


def test_finds_correct_subids_for_questions(
    parser: LimeSurveyParser, realistic_data: str
) -> None:
    assert np.array_equal(
        parser.parse_questions(realistic_data).columns.to_frame()[
            ["group_id", "question_id", "answer_id"]
        ],
        [[1.0, 2.0, 3.0], [2.0, 42.0, np.nan]],
        equal_nan=True,
    )
