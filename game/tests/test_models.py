import pytest
from django.core.exceptions import ValidationError

from game.models import Question


@pytest.mark.django_db
def test_question_is_saved_with_its_answer():
    Question.objects.create(text="How many bones does an adult human have?", answer=206)

    question = Question.objects.get()

    assert question.answer == 206
    assert question.category == ""


def test_question_shows_its_text():
    question = Question(text="How many keys does a piano have?", answer=88)

    assert str(question) == "How many keys does a piano have?"


def test_question_accepts_very_big_answers():
    question = Question(text="World population?", answer=8_000_000_000)

    question.full_clean()  # does not raise


def test_r9_question_answer_cannot_be_negative():
    question = Question(text="Invalid question", answer=-1)

    with pytest.raises(ValidationError):
        question.full_clean()
