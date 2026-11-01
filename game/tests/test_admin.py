import pytest
from django.urls import reverse

ADD_URL = reverse("admin:game_question_add")


@pytest.mark.django_db
def test_save_and_add_another_keeps_the_category(admin_client):
    response = admin_client.post(
        ADD_URL,
        {
            "text": "How many keys does a piano have?",
            "answer": 88,
            "category": "Music",
            "_addanother": "1",
        },
    )

    next_form = admin_client.get(response["Location"])

    assert next_form.context["adminform"].form.initial["category"] == "Music"


@pytest.mark.django_db
def test_save_and_add_another_without_category_leaves_it_empty(admin_client):
    response = admin_client.post(
        ADD_URL, {"text": "How many keys does a piano have?", "answer": 88, "_addanother": "1"}
    )

    assert "category" not in response["Location"]
