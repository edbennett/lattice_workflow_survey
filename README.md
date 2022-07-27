# limesurvey_parser
A simple parser for LimeSurvey's generated CSV files.

This is a very simple parser that reads a CSV file containing LimeSurvey results
and returns a `pandas.DataFrame` with convenient properties.

## Setup
```sh
# Install dependencies
pipenv install --dev

# Setup pre-commit and pre-push hooks
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

## Usage
You want to import the `LimeSurveyParser` and provide one of its parsing methods
with a python string of data, e.g.
```python3
>>>> from limesurvey_parser import LimeSurveyParser
>>>> parser = LimeSurveyParser()
>>>> with open('/path/to/file','r') as file:
>>>>    content = file.read()
>>>> questions = parser.parse_questions(content)
>>>> questions.T.query("question_id==50")
```
to get the answers to the 50th question. Similarly, you can parse the metadata,
i.e. start date, seed, ...
```python3
>>>> metadata = parser.parse_metadata(content)
>>>> metadata.T.query('title==Date submitted')
```
Please note that `pandas` seems to be quite reluctant with regards to `query`ing
a `pandas.MultiIndex` in the `columns`, so I found it to be necessary to
transpose before `query`ing.

## Credits
This package was created with Cookiecutter and the
[sourcery-ai/python-best-practices-cookiecutter](https://github.com/sourcery-ai/python-best-practices-cookiecutter)
project template.
