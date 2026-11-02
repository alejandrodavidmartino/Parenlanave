import pytest
from django.urls import reverse

from game.models import Game

HOME = reverse("game:home")


def new_game_data(*names, total_rounds=8):
    data = {"total_rounds": total_rounds}
    for number, name in enumerate(names, start=1):
        data[f"player_{number}"] = name
    return data


def test_home_shows_one_box_per_possible_player(client):
    response = client.get(HOME)

    assert response.content.count(b'name="player_') == 8


@pytest.mark.django_db
def test_creating_a_game_takes_you_to_its_page(client):
    response = client.post(HOME, new_game_data("Ana", "Luis", "Marta"))

    game = Game.objects.get()
    assert response.status_code == 302
    assert response["Location"] == reverse("game:detail", kwargs={"pk": game.pk})


@pytest.mark.django_db
def test_empty_boxes_are_ignored_and_names_are_trimmed(client):
    client.post(HOME, new_game_data("  Ana ", "", "Luis", "", "Marta"))

    game = Game.objects.get()
    assert [player.name for player in game.players.all()] == ["Ana", "Luis", "Marta"]


@pytest.mark.django_db
def test_chosen_number_of_rounds_is_used(client):
    client.post(HOME, new_game_data("Ana", "Luis", "Marta", total_rounds=5))

    assert Game.objects.get().total_rounds == 5


@pytest.mark.django_db
def test_r1_too_few_players_shows_an_error_and_creates_nothing(client):
    response = client.post(HOME, new_game_data("Ana", "Luis"))

    assert response.status_code == 200
    assert "Hacen falta entre 3 y 8 jugadores." in response.content.decode()
    assert not Game.objects.exists()


@pytest.mark.django_db
def test_game_page_shows_round_and_players(client):
    game = Game.start(["Ana", "Luis", "Marta"])

    response = client.get(reverse("game:detail", kwargs={"pk": game.pk}))

    content = response.content.decode()
    assert "Ronda 0 de 8" in content
    assert "Ana" in content and "Luis" in content and "Marta" in content


@pytest.mark.django_db
def test_unknown_game_gives_not_found(client):
    response = client.get(reverse("game:detail", kwargs={"pk": 999}))

    assert response.status_code == 404
