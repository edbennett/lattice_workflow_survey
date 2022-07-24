from limesurvey_parser import LimeSurveyParser
import pandas as pd


def test_returns_data_frame_on_empty_input():
    parser = LimeSurveyParser()
    assert type(parser.parse("")) == pd.DataFrame
