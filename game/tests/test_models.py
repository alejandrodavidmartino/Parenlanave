import random

import pytest
from django.core.exceptions import ValidationError

from game import engine
from game.models import Game, Question


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


@pytest.mark.django_db
def test_r1_game_starts_with_its_players_in_turn_order():
    game = Game.start(["Ana", "Luis", "Marta"])

    assert [player.name for player in game.players.all()] == ["Ana", "Luis", "Marta"]
    assert [player.position for player in game.players.all()] == [0, 1, 2]


@pytest.mark.django_db
def test_r1_game_with_too_few_players_is_not_created():
    with pytest.raises(ValueError):
        Game.start(["Ana", "Luis"])

    assert not Game.objects.exists()


@pytest.mark.django_db
def test_r2_game_has_8_rounds_by_default():
    game = Game.start(["Ana", "Luis", "Marta"])

    assert game.total_rounds == 8


@pytest.mark.django_db
def test_r2_number_of_rounds_can_be_chosen():
    game = Game.start(["Ana", "Luis", "Marta"], total_rounds=5)

    assert game.total_rounds == 5


@pytest.mark.django_db
def test_r3_players_start_with_0_coins():
    game = Game.start(["Ana", "Luis", "Marta"])

    assert all(player.coins == 0 for player in game.players.all())


@pytest.mark.django_db
def test_game_and_player_show_a_readable_name():
    game = Game.start(["Ana", "Luis", "Marta"])

    assert str(game).startswith(f"Game {game.pk} (")
    assert str(game.players.first()) == "Ana"


# Rounds.

NAMES = ["Ana", "Luis", "Marta"]


@pytest.fixture
def three_questions():
    return [Question.objects.create(text=f"Question {n}", answer=n * 100) for n in range(1, 4)]


@pytest.mark.django_db
def test_next_round_picks_a_question_and_an_opener(three_questions):
    game = Game.start(NAMES)

    game.next_round(random.Random(1))

    assert game.current_round == 1
    assert game.current_question in three_questions
    assert game.opener in {0, 1, 2}
    assert game.round_state is None  # waiting for the opening bid


@pytest.mark.django_db
def test_r6_questions_are_not_repeated_in_a_game(three_questions):
    game = Game.start(NAMES, total_rounds=3)
    rng = random.Random(1)

    asked = []
    for _ in range(3):
        game.next_round(rng)
        asked.append(game.current_question)

    assert sorted(question.pk for question in asked) == sorted(q.pk for q in three_questions)


@pytest.mark.django_db
def test_next_round_fails_when_there_are_no_questions_left(three_questions):
    game = Game.start(NAMES, total_rounds=5)
    rng = random.Random(1)
    for _ in range(3):
        game.next_round(rng)

    with pytest.raises(ValueError):
        game.next_round(rng)


@pytest.mark.django_db
def test_r2_no_more_rounds_after_the_last_one(three_questions):
    game = Game.start(NAMES, total_rounds=1)
    game.next_round(random.Random(1))

    with pytest.raises(ValueError):
        game.next_round(random.Random(1))


@pytest.mark.django_db
def test_round_in_progress_is_saved_and_loaded_from_the_database(three_questions):
    game = Game.start(NAMES)
    game.next_round(random.Random(1))
    game.open_round(100)
    round_ = game.load_round()
    engine.stay(round_, round_.turn_index)
    game.save_round(round_)

    reloaded = Game.objects.get(pk=game.pk).load_round()

    assert reloaded == round_
    assert reloaded.captain == game.opener
    assert reloaded.current_bid == 100


@pytest.mark.django_db
def test_phase_follows_the_round(three_questions):
    game = Game.start(NAMES)
    assert game.phase == "not_started"

    game.next_round(random.Random(1))
    assert game.phase == "opening"

    game.open_round(100)
    assert game.phase == "playing"

    round_ = game.load_round()
    engine.stay(round_, round_.turn_index)
    engine.stay(round_, round_.turn_index)
    game.save_round(round_)
    assert game.phase == "round_over"


# Revealing the answer and scoring.


def play_round(game, bid, *actions):
    """Open with `bid`, then play each action ("stay", "leave" or a number to raise)."""
    game.open_round(bid)
    round_ = game.load_round()
    for action in actions:
        if action == "stay":
            engine.stay(round_, round_.turn_index)
        elif action == "leave":
            engine.leave(round_, round_.turn_index)
        else:
            engine.raise_bid(round_, round_.turn_index, action)
    game.save_round(round_)


@pytest.fixture
def started_game():
    Question.objects.create(text="How many keys does a piano have?", answer=88)
    game = Game.start(NAMES, total_rounds=1)
    game.next_round(random.Random(1))
    return game


def coins_by_role(game):
    round_ = game.load_round()
    coins = {player.position: player.coins for player in game.players.all()}
    captain = coins.pop(round_.captain)
    return captain, coins


@pytest.mark.django_db
def test_r21_reveal_gives_coins_on_success(started_game):
    play_round(started_game, 80, "stay", "stay")  # 80 <= 88

    started_game.reveal()

    captain, others = coins_by_role(started_game)
    assert captain == 4
    assert sorted(others.values()) == [2, 2]


@pytest.mark.django_db
def test_r22_r25_reveal_on_failure_never_goes_below_zero(started_game):
    play_round(started_game, 90, "leave", "stay")  # 90 > 88

    started_game.reveal()

    captain, others = coins_by_role(started_game)
    assert captain == 0  # would be -1 (R25)
    assert sorted(others.values()) == [0, 2]  # crew 0, deserter +2


@pytest.mark.django_db
def test_round_scores_are_kept_to_show_them(started_game):
    play_round(started_game, 90, "leave", "leave")  # lone captain fails (R24)

    started_game.reveal()

    round_ = started_game.load_round()
    assert started_game.round_scores[round_.captain] == -1
    assert sorted(started_game.round_scores) == [-1, 2, 2]


@pytest.mark.django_db
def test_phase_after_revealing_the_last_round_is_game_over(started_game):
    play_round(started_game, 80, "stay", "stay")
    assert started_game.phase == "round_over"

    started_game.reveal()

    assert started_game.phase == "game_over"


@pytest.mark.django_db
def test_phase_after_revealing_a_round_that_is_not_the_last(started_game):
    started_game.total_rounds = 2
    play_round(started_game, 80, "stay", "stay")

    started_game.reveal()

    assert started_game.phase == "revealed"


@pytest.mark.django_db
def test_r4_winners_are_the_players_with_most_coins(started_game):
    play_round(started_game, 80, "stay", "leave")  # captain 4, crew 2, deserter 0
    started_game.reveal()

    winners = started_game.winners()

    assert [player.position for player in winners] == [started_game.load_round().captain]
