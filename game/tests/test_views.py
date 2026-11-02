import pytest
from django.urls import reverse

from game.models import Game, Question

HOME = reverse("game:new")


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
    assert "Ronda 0/8" in content
    assert "Ana" in content and "Luis" in content and "Marta" in content


@pytest.mark.django_db
def test_unknown_game_gives_not_found(client):
    response = client.get(reverse("game:detail", kwargs={"pk": 999}))

    assert response.status_code == 404


# Playing a round. HTMX requests carry the HX-Request header.

HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def game():
    Question.objects.create(text="How many keys does a piano have?", answer=88)
    return Game.start(["Ana", "Luis", "Marta"])


def url(name, game):
    return reverse(f"game:{name}", kwargs={"pk": game.pk})


def refresh(game):
    return Game.objects.get(pk=game.pk)


@pytest.mark.django_db
def test_starting_the_game_shows_the_question_and_who_opens(client, game):
    response = client.post(url("next_round", game), **HTMX)

    game = refresh(game)
    content = response.content.decode()
    assert game.phase == "opening"
    assert "How many keys does a piano have?" in content
    assert "Abre la ronda:" in content
    assert game.players.all()[game.opener].name in content


@pytest.mark.django_db
def test_htmx_gets_only_the_board_and_a_normal_form_gets_redirected(client, game):
    htmx_response = client.post(url("next_round", game), **HTMX)

    assert 'id="board"' in htmx_response.content.decode()
    assert "<html" not in htmx_response.content.decode()


@pytest.mark.django_db
def test_without_htmx_actions_redirect_to_the_game_page(client, game):
    response = client.post(url("next_round", game))

    assert response.status_code == 302
    assert response["Location"] == url("detail", game)


@pytest.mark.django_db
def test_opening_bid_starts_the_round(client, game):
    client.post(url("next_round", game), **HTMX)

    client.post(url("open_round", game), {"bid": "50"}, **HTMX)

    game = refresh(game)
    assert game.phase == "playing"
    assert game.load_round().current_bid == 50


@pytest.mark.django_db
def test_r9_invalid_opening_bid_shows_an_error(client, game):
    client.post(url("next_round", game), **HTMX)

    response = client.post(url("open_round", game), {"bid": "-3"}, **HTMX)

    assert "Esa jugada no está permitida." in response.content.decode()
    assert refresh(game).phase == "opening"


def play(client, game, action, bid=""):
    turn = refresh(game).load_round().turn_index
    return client.post(url("play", game), {"player": turn, "action": action, "bid": bid}, **HTMX)


@pytest.mark.django_db
def test_a_full_round_can_be_played(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "50"}, **HTMX)

    play(client, game, "raise", "70")
    play(client, game, "leave")
    response = play(client, game, "stay")

    round_ = refresh(game).load_round()
    assert refresh(game).phase == "round_over"
    assert round_.current_bid == 70
    assert "Ronda terminada" in response.content.decode()


@pytest.mark.django_db
def test_r14_raise_not_higher_shows_an_error_and_changes_nothing(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "50"}, **HTMX)
    before = refresh(game).round_state

    response = play(client, game, "raise", "50")

    assert "Esa jugada no está permitida." in response.content.decode()
    assert refresh(game).round_state == before


@pytest.mark.django_db
def test_r17_a_double_tap_from_the_previous_player_is_rejected(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "50"}, **HTMX)
    first = refresh(game).load_round().turn_index
    client.post(url("play", game), {"player": first, "action": "stay"}, **HTMX)

    response = client.post(url("play", game), {"player": first, "action": "stay"}, **HTMX)

    assert "Esa jugada no está permitida." in response.content.decode()


@pytest.mark.django_db
def test_playing_before_the_round_starts_is_rejected(client, game):
    response = client.post(url("play", game), {"player": 0, "action": "stay"}, **HTMX)

    assert "Esa jugada no está permitida." in response.content.decode()


@pytest.mark.django_db
def test_unknown_action_is_rejected(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "50"}, **HTMX)

    response = play(client, game, "dance")

    assert "Esa jugada no está permitida." in response.content.decode()


@pytest.mark.django_db
def test_actions_only_accept_post(client, game):
    response = client.get(url("next_round", game))

    assert response.status_code == 405


@pytest.mark.django_db
def test_next_round_is_rejected_while_a_round_is_being_played(client, game):
    client.post(url("next_round", game), **HTMX)

    response = client.post(url("next_round", game), **HTMX)

    assert "Esa jugada no está permitida." in response.content.decode()


@pytest.mark.django_db
def test_next_round_explains_when_there_are_no_questions_left(client):
    game = Game.start(["Ana", "Luis", "Marta"])  # no questions in the database

    response = client.post(url("next_round", game), **HTMX)

    assert "No quedan rondas o preguntas." in response.content.decode()


@pytest.mark.django_db
def test_opening_is_rejected_before_the_round_starts(client, game):
    response = client.post(url("open_round", game), {"bid": "50"}, **HTMX)

    assert "Esa jugada no está permitida." in response.content.decode()


@pytest.mark.django_db
def test_opening_bid_must_be_a_number(client, game):
    client.post(url("next_round", game), **HTMX)

    response = client.post(url("open_round", game), {"bid": "mucho"}, **HTMX)

    assert "Esa jugada no está permitida." in response.content.decode()


@pytest.mark.django_db
def test_without_htmx_errors_show_the_whole_page(client, game):
    response = client.post(url("open_round", game), {"bid": "50"})

    content = response.content.decode()
    assert response.status_code == 200
    assert "<html" in content
    assert "Esa jugada no está permitida." in content


# Revealing and the end of the game.


def finish_round(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "50"}, **HTMX)
    play(client, game, "stay")
    play(client, game, "stay")


@pytest.mark.django_db
def test_reveal_shows_the_answer_and_the_coins(client, game):
    finish_round(client, game)

    response = client.post(url("reveal", game), **HTMX)

    content = response.content.decode()
    assert "La respuesta era" in content and "88" in content
    assert "¡El barco zarpa!" in content  # 50 <= 88
    assert "+4" in content and "+2" in content


@pytest.mark.django_db
def test_reveal_is_rejected_before_the_round_is_over(client, game):
    client.post(url("next_round", game), **HTMX)

    response = client.post(url("reveal", game), **HTMX)

    assert "Esa jugada no está permitida." in response.content.decode()


@pytest.mark.django_db
def test_coins_are_given_only_once(client, game):
    finish_round(client, game)
    client.post(url("reveal", game), **HTMX)

    client.post(url("reveal", game), **HTMX)

    assert sorted(player.coins for player in game.players.all()) == [2, 2, 4]


@pytest.mark.django_db
def test_next_round_needs_the_answer_revealed_first(client, game):
    game.total_rounds = 2
    game.save()
    finish_round(client, game)

    response = client.post(url("next_round", game), **HTMX)

    assert "Esa jugada no está permitida." in response.content.decode()


@pytest.mark.django_db
def test_r4_last_round_shows_the_winner(client, game):
    game.total_rounds = 1
    game.save()
    finish_round(client, game)

    response = client.post(url("reveal", game), **HTMX)

    captain = refresh(game).load_round().captain
    winner = game.players.all()[captain].name
    content = response.content.decode()
    assert "Fin de la partida" in content
    assert f"Gana {winner}" in content
    assert "Nueva partida" in content


@pytest.mark.django_db
def test_r4_a_tie_shows_every_winner(client, game):
    game.total_rounds = 1
    game.save()
    game.players.update(coins=10)  # the round below adds 4, 2 and 2
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "500"}, **HTMX)  # fails: 500 > 88
    play(client, game, "leave")
    play(client, game, "leave")  # lone captain fails: -1, deserters +2 each

    response = client.post(url("reveal", game), **HTMX)

    assert "Empate:" in response.content.decode()
    assert "¡Naufragio!" in response.content.decode()


# Pixel art screen: pass the phone, rules, scoreboard and podium.


@pytest.mark.django_db
def test_pass_the_phone_curtain_names_the_next_player(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "50"}, **HTMX)

    response = play(client, game, "stay")

    next_player = refresh(game).players.all()[refresh(game).load_round().turn_index].name
    content = response.content.decode()
    assert "Pasa el móvil a" in content
    assert f"Soy {next_player}" in content


@pytest.mark.django_db
def test_no_curtain_after_a_rejected_move(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "50"}, **HTMX)

    response = play(client, game, "raise", "10")  # not higher: same player tries again

    assert "Pasa el móvil a" not in response.content.decode()


@pytest.mark.django_db
def test_rules_window_shows_the_engine_scoring(client, game):
    response = client.get(url("detail", game))

    content = response.content.decode()
    assert "Cómo se juega" in content
    assert "<td>⚓ Capitán</td><td>4</td><td>-1</td>" in content


@pytest.mark.django_db
def test_scoreboard_lists_players_by_coins(client, game):
    luis = game.players.get(name="Luis")
    luis.coins = 9
    luis.save()

    response = client.get(url("detail", game))

    ranking = response.context["ranking"]
    assert [player["name"] for player in ranking] == ["Luis", "Ana", "Marta"]


@pytest.mark.django_db
def test_revealed_round_shows_each_players_role(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "50"}, **HTMX)
    play(client, game, "leave")
    play(client, game, "stay")

    response = client.post(url("reveal", game), **HTMX)

    roles = sorted(player["role"] for player in response.context["players"])
    assert roles == ["capitán", "desertor", "tripulante"]


@pytest.mark.django_db
def test_podium_puts_the_winner_in_the_middle(client, game):
    game.total_rounds = 1
    game.save()
    finish_round(client, game)

    response = client.post(url("reveal", game), **HTMX)

    podium = response.context["podium"]
    assert [step["place"] for step in podium] == [2, 1, 3]
    assert podium[1]["name"] == response.context["winners"][0]


# "+ Añadir jugador" on the home screen.

VISIBLE_ROW = '<div data-player class="flex gap-2">'
HIDDEN_ROW = '<div data-player class="flex gap-2" hidden>'


def test_home_shows_three_name_boxes_and_hides_the_rest(client):
    content = client.get(HOME).content.decode()

    assert content.count(VISIBLE_ROW) == 3
    assert content.count(HIDDEN_ROW) == 5
    assert "+ Añadir jugador" in content


@pytest.mark.django_db
def test_names_typed_before_an_error_stay_visible(client):
    response = client.post(HOME, new_game_data("Ana", "", "", "", "Luis"))  # only 2 names

    content = response.content.decode()
    assert content.count(VISIBLE_ROW) == 5  # up to the box with "Luis"
    assert 'value="Luis"' in content


@pytest.mark.django_db
def test_add_player_button_disappears_when_every_box_shows(client):
    names = ["Ana", "Luis", "Marta", "Pablo", "Eva", "Juan", "Sara", ""]

    response = client.post(HOME, {**new_game_data(*names), "total_rounds": 0})  # rounds error

    content = response.content.decode()
    assert content.count(VISIBLE_ROW) == 7
    assert "+ Añadir jugador" in content

    names[-1] = "Leo"
    response = client.post(HOME, {**new_game_data(*names), "total_rounds": 0})

    assert "+ Añadir jugador" not in response.content.decode()


# Player colours.


@pytest.mark.django_db
def test_players_get_the_colours_chosen_in_the_form(client):
    data = new_game_data("Ana", "Luis", "Marta")
    data.update(colour_1="green", colour_2="pink", colour_3="brown")

    client.post(HOME, data)

    colours = [player.colour for player in Game.objects.get().players.all()]
    assert colours == ["green", "pink", "brown"]


@pytest.mark.django_db
def test_without_colours_each_player_gets_a_different_default(client):
    client.post(HOME, new_game_data("Ana", "", "Luis", "Marta"))

    colours = [player.colour for player in Game.objects.get().players.all()]
    assert colours == ["red", "yellow", "green"]  # the defaults of rows 1, 3 and 4


@pytest.mark.django_db
def test_two_players_with_the_same_colour_shows_an_error(client):
    data = new_game_data("Ana", "Luis", "Marta")
    data.update(colour_1="green", colour_2="green", colour_3="brown")

    response = client.post(HOME, data)

    assert "Cada jugador necesita un color distinto." in response.content.decode()
    assert not Game.objects.exists()


def test_each_name_box_has_a_colour_button(client):
    content = client.get(HOME).content.decode()

    assert content.count('onclick="cycleColour(this)"') == 8
    assert 'id="player-colours"' in content


@pytest.mark.django_db
def test_pass_the_phone_curtain_uses_the_players_colour(client, game):
    client.post(url("next_round", game), **HTMX)

    response = client.post(url("open_round", game), {"bid": "50"}, **HTMX)

    player = refresh(game).players.all()[refresh(game).load_round().turn_index]
    content = response.content.decode()
    assert f"background: {player.muted_background}" in content  # toned down, kind to the eyes
    assert f"border-color: {player.background}" in content  # the bright colour frames the sailor
    assert f'fill="{player.background}"' in content  # the sailor's stripes


def test_colour_buttons_show_how_to_change_the_colour(client):
    content = client.get(HOME).content.decode()

    assert content.count(">↻</button>") == 8
    assert "para cambiar el color" in content


@pytest.mark.django_db
def test_lone_captain_who_makes_it_takes_all_the_loot(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "10"}, **HTMX)  # 10 <= 88
    play(client, game, "leave")
    play(client, game, "leave")

    response = client.post(url("reveal", game), **HTMX)

    assert "Se lleva todo el botín." in response.content.decode()


@pytest.mark.django_db
def test_lone_captain_who_sinks_makes_the_deserters_celebrate(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "500"}, **HTMX)  # 500 > 88
    play(client, game, "leave")
    play(client, game, "leave")

    response = client.post(url("reveal", game), **HTMX)

    assert "¡y los desertores lo celebran!" in response.content.decode()


# Full screen reveal with suspense.


@pytest.mark.django_db
def test_revealing_brings_the_full_screen_suspense_scene(client, game):
    finish_round(client, game)  # Ana, Luis or Marta opened with 50; the answer is 88

    response = client.post(url("reveal", game), **HTMX)

    content = response.content.decode()
    assert 'data-reveal hidden data-answer="88" data-bid="50"' in content
    assert "¿Zarpará o se hundirá?" in content
    assert 'class="voyage-wait box-px p-0"' in content  # the ending waits for the counter


@pytest.mark.django_db
def test_reloading_the_page_does_not_play_the_suspense_again(client, game):
    finish_round(client, game)
    client.post(url("reveal", game), **HTMX)

    response = client.get(url("detail", game))

    assert "data-reveal" not in response.content.decode()


@pytest.mark.django_db
def test_revealed_round_lists_who_is_aboard_and_who_stayed_on_the_dock(client, game):
    client.post(url("next_round", game), **HTMX)
    client.post(url("open_round", game), {"bid": "50"}, **HTMX)
    play(client, game, "leave")
    play(client, game, "stay")

    response = client.post(url("reveal", game), **HTMX)

    aboard = [player["name"] for player in response.context["aboard"]]
    ashore = [player["name"] for player in response.context["ashore"]]
    captain = game.players.all()[refresh(game).load_round().captain].name
    assert aboard[0] == captain  # the captain goes first, with the anchor
    assert len(aboard) == 2 and len(ashore) == 1
    assert "A bordo:" in response.content.decode()
    assert "En el muelle:" in response.content.decode()


@pytest.mark.django_db
def test_pass_the_phone_tells_the_opener_to_bid(client, game):
    response = client.post(url("next_round", game), **HTMX)

    assert "Te toca abrir: di el primer número." in response.content.decode()


@pytest.mark.django_db
def test_pass_the_phone_shows_the_captain_and_bid_to_beat(client, game):
    client.post(url("next_round", game), **HTMX)

    response = client.post(url("open_round", game), {"bid": "50"}, **HTMX)

    captain = refresh(game).players.all()[refresh(game).load_round().captain].name
    content = response.content.decode()
    assert f"Capitán: {captain} con" in content
    assert "nadie más mire" not in content
