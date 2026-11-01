"""Game rules engine.

Pure Python: this module must not import anything from Django, so the same rules
can be tested on their own and reused by the online version later on.
The rules it implements are described in RULES.md.
"""

import random
from dataclasses import asdict, dataclass
from enum import Enum

# Game setup (R1-R3).
MIN_PLAYERS = 3
MAX_PLAYERS = 8
DEFAULT_ROUNDS = 8
STARTING_COINS = 0

# Coins won (or lost, if negative) at the end of a round (R21-R24).
CAPTAIN_SUCCESS = 4
CREW_SUCCESS = 2
DESERTER_SUCCESS = 0
LONE_CAPTAIN_SUCCESS = 6
CAPTAIN_FAILURE = -1
CREW_FAILURE = 0
DESERTER_FAILURE = 2


class InvalidMoveError(Exception):
    """Raised when a move breaks the rules. The round is left unchanged (R17)."""


class PlayerStatus(Enum):
    """Whether a player is still taking part in the current round."""

    ON_BOARD = "on_board"
    LEFT = "left"


@dataclass
class Player:
    """A player in a round. Everyone starts each round on board (R5)."""

    name: str
    status: PlayerStatus = PlayerStatus.ON_BOARD


@dataclass
class Round:
    """The state of one round.

    `captain` and `turn_index` are positions in `players`, which is also the turn
    order (R10).
    """

    players: list[Player]
    captain: int
    current_bid: int
    turn_index: int

    @property
    def is_over(self) -> bool:
        """The round ends when the turn gets back to the captain (R18)."""
        return self.turn_index == self.captain


@dataclass
class RoundResult:
    """What happened in a finished round: everything needed to score it.

    `captain`, `crew` and `deserters` are positions in the players list.
    """

    captain: int
    crew: list[int]
    deserters: list[int]
    bid: int
    answer: int

    @property
    def success(self) -> bool:
        """The mission succeeds if the captain's bid is not above the answer (R20)."""
        return self.bid <= self.answer

    @property
    def lone_captain(self) -> bool:
        """Everyone else left the ship (R19)."""
        return not self.crew


def _check_bid(bid: int) -> None:
    """A bid must be a whole number, 0 or greater (R9)."""
    if not isinstance(bid, int) or bid < 0:
        raise InvalidMoveError(f"Bid must be a whole number, 0 or greater: {bid!r}")


def _check_turn(round_: Round, player: int) -> None:
    """Only the player whose turn it is can play, and only while the round lasts (R17).

    Players who left never get the turn back (R11), so this also stops them.
    """
    if round_.is_over:
        raise InvalidMoveError("The round is over")
    if player != round_.turn_index:
        raise InvalidMoveError(f"It is not player {player}'s turn")


def _advance_turn(round_: Round) -> None:
    """Pass the turn to the next player on board, skipping those who left (R10, R11)."""
    index = (round_.turn_index + 1) % len(round_.players)
    while round_.players[index].status == PlayerStatus.LEFT:
        index = (index + 1) % len(round_.players)
    round_.turn_index = index


def choose_opener(player_count: int, rng: random.Random) -> int:
    """Pick at random who opens the round (R7). Returns a position in the players list."""
    return rng.randrange(player_count)


def start_round(names: list[str], opener: int, opening_bid: int) -> Round:
    """Start a round where `opener` makes the opening bid and becomes captain (R8).

    Everyone starts on board (R5) and the first turn goes to the player after the
    opener, wrapping around the list (R10).
    """
    _check_bid(opening_bid)
    players = [Player(name=name) for name in names]
    return Round(
        players=players,
        captain=opener,
        current_bid=opening_bid,
        turn_index=(opener + 1) % len(players),
    )


def stay(round_: Round, player: int) -> None:
    """The player backs the current bid and the turn moves on (R12)."""
    _check_turn(round_, player)
    _advance_turn(round_)


def leave(round_: Round, player: int) -> None:
    """The player leaves the ship until the end of the round (R13)."""
    _check_turn(round_, player)
    round_.players[player].status = PlayerStatus.LEFT
    _advance_turn(round_)


def raise_bid(round_: Round, player: int, bid: int) -> None:
    """The player bids strictly higher and becomes the new captain (R14).

    The previous captain stays on board (R15). The captain can never raise their own
    bid, because by the time the turn gets back to them the round is over (R16, R18).
    """
    _check_turn(round_, player)
    _check_bid(bid)
    if bid <= round_.current_bid:
        raise InvalidMoveError(f"Bid must be higher than {round_.current_bid}: {bid}")
    round_.captain = player
    round_.current_bid = bid
    _advance_turn(round_)


def finish_round(round_: Round, answer: int) -> RoundResult:
    """Reveal the real answer once the round is over and say who was where (R20)."""
    if not round_.is_over:
        raise InvalidMoveError("The round is not over yet")
    crew = [
        index
        for index, player in enumerate(round_.players)
        if player.status == PlayerStatus.ON_BOARD and index != round_.captain
    ]
    deserters = [
        index for index, player in enumerate(round_.players) if player.status == PlayerStatus.LEFT
    ]
    return RoundResult(
        captain=round_.captain,
        crew=crew,
        deserters=deserters,
        bid=round_.current_bid,
        answer=answer,
    )


def score_round(result: RoundResult) -> dict[int, int]:
    """Coins each player wins or loses this round, by position (R21-R24).

    A lone captain who fails scores like any failed mission (R24).
    """
    if result.success:
        captain = LONE_CAPTAIN_SUCCESS if result.lone_captain else CAPTAIN_SUCCESS
        crew = CREW_SUCCESS
        deserter = DESERTER_SUCCESS
    else:
        captain = CAPTAIN_FAILURE
        crew = CREW_FAILURE
        deserter = DESERTER_FAILURE

    deltas = {result.captain: captain}
    for player in result.crew:
        deltas[player] = crew
    for player in result.deserters:
        deltas[player] = deserter
    return deltas


def apply_scores(coins: list[int], deltas: dict[int, int]) -> list[int]:
    """Add each player's coins for the round. Nobody goes below 0 (R25)."""
    return [max(0, total + deltas.get(player, 0)) for player, total in enumerate(coins)]


def check_player_count(count: int) -> None:
    """A game has between 3 and 8 players (R1)."""
    if not MIN_PLAYERS <= count <= MAX_PLAYERS:
        raise ValueError(f"A game needs {MIN_PLAYERS} to {MAX_PLAYERS} players, not {count}")


def winners(coins: list[int]) -> list[int]:
    """Positions of the players with the most coins. Ties share the win (R4)."""
    best = max(coins)
    return [player for player, total in enumerate(coins) if total == best]


def round_to_dict(round_: Round) -> dict:
    """Turn a round into plain data (text and numbers) so it can be saved as JSON."""
    data = asdict(round_)
    data["players"] = [
        {"name": player.name, "status": player.status.value} for player in round_.players
    ]
    return data


def round_from_dict(data: dict) -> Round:
    """Rebuild a round saved with `round_to_dict`."""
    players = [
        Player(name=player["name"], status=PlayerStatus(player["status"]))
        for player in data["players"]
    ]
    return Round(
        players=players,
        captain=data["captain"],
        current_bid=data["current_bid"],
        turn_index=data["turn_index"],
    )
