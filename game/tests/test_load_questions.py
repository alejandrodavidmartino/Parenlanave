import json

import pytest
from django.core.management import call_command

from game.models import Question


@pytest.mark.django_db
def test_load_questions_adds_every_question_in_the_default_file():
    call_command("load_questions")

    assert Question.objects.count() > 0
    assert all(question.answer >= 0 for question in Question.objects.all())


@pytest.mark.django_db
def test_load_questions_twice_does_not_duplicate(tmp_path):
    file = tmp_path / "questions.json"
    file.write_text(json.dumps([{"text": "How many keys?", "answer": 88}]), encoding="utf-8")

    call_command("load_questions", file)
    call_command("load_questions", file)

    assert Question.objects.count() == 1


@pytest.mark.django_db
def test_load_questions_does_not_overwrite_existing_questions(tmp_path):
    Question.objects.create(text="How many keys?", answer=80, category="Edited in admin")
    file = tmp_path / "questions.json"
    file.write_text(json.dumps([{"text": "How many keys?", "answer": 88}]), encoding="utf-8")

    call_command("load_questions", file)

    question = Question.objects.get()
    assert question.answer == 80
    assert question.category == "Edited in admin"
