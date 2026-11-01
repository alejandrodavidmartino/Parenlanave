import copy
import random

import pytest

from game.engine import (
    InvalidMoveError,
    Player,
    PlayerStatus,
    RoundResult,
    apply_scores,
    choose_opener,
    finish_round,
    leave,
    raise_bid,
    score_round,
    start_round,
    stay,
)

NAMES = ["Ana", "Luis", "Marta"]
ANA, LUIS, MARTA = 0, 1, 2


def test_r5_new_player_starts_on_board():
    player = Player(name="Ana")

    assert player.status == PlayerStatus.ON_BOARD


def test_r5_everyone_starts_the_round_on_board():
    round_ = start_round(NAMES, opener=0, opening_bid=100)

    assert all(player.status == PlayerStatus.ON_BOARD for player in round_.players)


def test_r7_same_seed_picks_same_opener():
    first = choose_opener(len(NAMES), random.Random(42))
    second = choose_opener(len(NAMES), random.Random(42))

    assert first == second


def test_r7_any_player_can_open():
    openers = {choose_opener(len(NAMES), random.Random(seed)) for seed in range(50)}

    assert openers == {0, 1, 2}


def test_r8_opener_becomes_captain_with_opening_bid():
    round_ = start_round(NAMES, opener=1, opening_bid=120)

    assert round_.captain == 1
    assert round_.current_bid == 120


def test_r9_opening_bid_can_be_zero():
    round_ = start_round(NAMES, opener=0, opening_bid=0)

    assert round_.current_bid == 0


def test_r9_opening_bid_cannot_be_negative():
    with pytest.raises(InvalidMoveError):
        start_round(NAMES, opener=0, opening_bid=-5)


def test_r9_opening_bid_cannot_have_decimals():
    with pytest.raises(InvalidMoveError):
        start_round(NAMES, opener=0, opening_bid=2.5)


def test_r10_first_turn_is_the_player_after_the_opener():
    round_ = start_round(NAMES, opener=0, opening_bid=100)

    assert round_.turn_index == 1


def test_r10_first_turn_wraps_around_after_the_last_player():
    round_ = start_round(NAMES, opener=2, opening_bid=100)

    assert round_.turn_index == 0


# Actions. In every round below Ana opens with 100, so Luis plays first.


def test_r12_stay_passes_the_turn_and_changes_nothing_else():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)

    stay(round_, LUIS)

    assert round_.turn_index == MARTA
    assert round_.captain == ANA
    assert round_.current_bid == 100
    assert round_.players[LUIS].status == PlayerStatus.ON_BOARD


def test_r13_leave_takes_the_player_off_the_ship():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)

    leave(round_, LUIS)

    assert round_.players[LUIS].status == PlayerStatus.LEFT
    assert round_.turn_index == MARTA


def test_r13_a_player_who_left_cannot_play_again():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    leave(round_, LUIS)

    with pytest.raises(InvalidMoveError):
        stay(round_, LUIS)  # changing their mind is not allowed


def test_r11_players_who_left_are_skipped():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    leave(round_, LUIS)
    raise_bid(round_, MARTA, 150)

    stay(round_, ANA)

    assert round_.turn_index == MARTA  # Luis (1) is skipped


def test_r14_raise_makes_a_new_captain_with_the_new_bid():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)

    raise_bid(round_, LUIS, 150)

    assert round_.captain == LUIS
    assert round_.current_bid == 150
    assert round_.turn_index == MARTA


def test_r14_raise_must_be_higher_not_equal():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)

    with pytest.raises(InvalidMoveError):
        raise_bid(round_, LUIS, 100)


def test_r14_raise_must_be_higher_not_lower():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)

    with pytest.raises(InvalidMoveError):
        raise_bid(round_, LUIS, 90)


def test_r9_raise_cannot_have_decimals():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)

    with pytest.raises(InvalidMoveError):
        raise_bid(round_, LUIS, 150.5)


def test_r15_previous_captain_stays_on_board_and_plays_again():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    raise_bid(round_, LUIS, 150)
    stay(round_, MARTA)

    assert round_.players[ANA].status == PlayerStatus.ON_BOARD
    assert round_.turn_index == ANA


def test_r16_captain_cannot_raise_their_own_bid():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    stay(round_, LUIS)
    stay(round_, MARTA)

    with pytest.raises(InvalidMoveError):
        raise_bid(round_, ANA, 200)


def test_r17_playing_out_of_turn_is_rejected():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)

    with pytest.raises(InvalidMoveError):
        stay(round_, MARTA)  # it's Luis's turn


def test_r17_rejected_move_leaves_the_round_unchanged():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    before = copy.deepcopy(round_)

    with pytest.raises(InvalidMoveError):
        raise_bid(round_, LUIS, 90)

    assert round_ == before


# End of the round and result.


def test_r18_round_is_not_over_while_others_still_have_to_play():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)

    stay(round_, LUIS)

    assert not round_.is_over


def test_r18_round_ends_when_the_turn_gets_back_to_the_captain():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    stay(round_, LUIS)

    stay(round_, MARTA)

    assert round_.is_over


def test_r18_a_raise_makes_everyone_decide_again():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    raise_bid(round_, LUIS, 150)
    stay(round_, MARTA)

    assert not round_.is_over  # Ana still has to decide on Luis's bid

    stay(round_, ANA)

    assert round_.is_over


def test_r19_round_ends_when_everyone_else_leaves():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    leave(round_, LUIS)
    leave(round_, MARTA)

    result = finish_round(round_, answer=500)

    assert round_.is_over
    assert result.lone_captain


def test_r19_not_a_lone_captain_if_someone_stays():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    leave(round_, LUIS)
    stay(round_, MARTA)

    result = finish_round(round_, answer=500)

    assert not result.lone_captain


def test_result_says_who_is_captain_crew_and_deserter():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    raise_bid(round_, LUIS, 150)
    leave(round_, MARTA)
    stay(round_, ANA)

    result = finish_round(round_, answer=200)

    assert result.captain == LUIS
    assert result.crew == [ANA]
    assert result.deserters == [MARTA]
    assert result.bid == 150


def test_cannot_reveal_the_answer_before_the_round_is_over():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)

    with pytest.raises(InvalidMoveError):
        finish_round(round_, answer=200)


def _finished_round(answer):
    """A round where Ana opens with 100 and everyone stays."""
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    stay(round_, LUIS)
    stay(round_, MARTA)
    return finish_round(round_, answer=answer)


def test_r20_success_when_bid_is_below_the_answer():
    assert _finished_round(answer=150).success


def test_r20_success_when_bid_equals_the_answer():
    assert _finished_round(answer=100).success


def test_r20_failure_when_bid_is_above_the_answer():
    assert not _finished_round(answer=99).success


# Scoring. Results are built by hand: Luis is captain with 150.


def test_r21_success_scores():
    result = RoundResult(captain=LUIS, crew=[ANA], deserters=[MARTA], bid=150, answer=200)

    assert score_round(result) == {LUIS: 4, ANA: 2, MARTA: 0}


def test_r21_every_crew_member_scores():
    result = RoundResult(captain=LUIS, crew=[ANA, MARTA], deserters=[], bid=150, answer=200)

    assert score_round(result) == {LUIS: 4, ANA: 2, MARTA: 2}


def test_r22_failure_scores():
    result = RoundResult(captain=LUIS, crew=[ANA], deserters=[MARTA], bid=150, answer=100)

    assert score_round(result) == {LUIS: -1, ANA: 0, MARTA: 2}


def test_r23_lone_captain_success_scores():
    result = RoundResult(captain=LUIS, crew=[], deserters=[ANA, MARTA], bid=150, answer=200)

    assert score_round(result) == {LUIS: 6, ANA: 0, MARTA: 0}


def test_r24_lone_captain_failure_scores_like_any_failure():
    result = RoundResult(captain=LUIS, crew=[], deserters=[ANA, MARTA], bid=150, answer=100)

    assert score_round(result) == {LUIS: -1, ANA: 2, MARTA: 2}


def test_r25_coins_are_added_to_each_player():
    assert apply_scores([5, 3, 0], {ANA: 4, LUIS: 2, MARTA: 0}) == [9, 5, 0]


def test_r25_coins_never_go_below_zero():
    assert apply_scores([0, 3, 0], {ANA: -1, LUIS: -1, MARTA: 2}) == [0, 2, 2]


def test_full_round_from_start_to_coins():
    round_ = start_round(NAMES, opener=ANA, opening_bid=100)
    raise_bid(round_, LUIS, 150)
    leave(round_, MARTA)
    stay(round_, ANA)

    result = finish_round(round_, answer=206)
    coins = apply_scores([0, 0, 0], score_round(result))

    assert coins == [2, 4, 0]  # Ana crew, Luis captain, Marta deserter
