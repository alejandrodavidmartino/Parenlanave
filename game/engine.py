"""Game rules engine.

Pure Python: this module must not import anything from Django, so the same rules
can be tested on their own and reused by the online version later on.
The rules it implements are described in RULES.md.
"""

import random
from dataclasses import asdict, dataclass, field
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

# Treasure question (R26-R27): how often it comes up, and the captain's coins in it.
# The crew and the deserters score as usual.
TREASURE_CHANCE = 0.1
TREASURE_CAPTAIN_SUCCESS = 8
TREASURE_LONE_CAPTAIN_SUCCESS = 12
TREASURE_CAPTAIN_FAILURE = -4

# Órdago (R31-R32). It scores the same in a treasure question (R33).
ORDAGO_HIT = 10
ORDAGO_MISS = -3
ORDAGO_OTHERS_ON_MISS = 1


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

    The engine only sees one round, but the órdago is once per game (R29), so the
    round is told who already spent theirs in earlier rounds (`ordago_spent`).
    """

    players: list[Player]
    captain: int
    current_bid: int
    turn_index: int
    ordago_spent: list[int] = field(default_factory=list)
    # Who called an órdago this round, and their number. None if nobody did.
    ordago_caller: int | None = None
    ordago_bid: int | None = None

    @property
    def is_over(self) -> bool:
        """The round ends when the turn gets back to the captain (R18), or at once
        when someone calls an órdago (R30)."""
        return self.ordago_caller is not None or self.turn_index == self.captain


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
    ordago_caller: int | None = None
    ordago_bid: int | None = None

    @property
    def ordago_hit(self) -> bool:
        """An órdago is only right with the exact answer (R31)."""
        return self.ordago_caller is not None and self.ordago_bid == self.answer

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


def is_treasure_round(rng: random.Random) -> bool:
    """Decide at random whether this round is a treasure question (R26)."""
    return rng.random() < TREASURE_CHANCE


def start_round(names: list[str], opener: int, opening_bid: int, ordago_spent=()) -> Round:
    """Start a round where `opener` makes the opening bid and becomes captain (R8).

    Everyone starts on board (R5) and the first turn goes to the player after the
    opener, wrapping around the list (R10). `ordago_spent` lists who already called
    their órdago earlier in the game (R29).
    """
    _check_bid(opening_bid)
    players = [Player(name=name) for name in names]
    return Round(
        players=players,
        captain=opener,
        current_bid=opening_bid,
        turn_index=(opener + 1) % len(players),
        ordago_spent=list(ordago_spent),
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


def call_ordago(round_: Round, player: int, bid: int) -> None:
    """The player bets that `bid` is exactly the answer and the round freezes (R28-R30).

    It is a different bet from raising, so it doesn't need to beat the current bid.
    The turn doesn't move on: the round is over now. The opener can't use it for the
    opening bid because `start_round` has no way to call it.
    """
    _check_turn(round_, player)
    _check_bid(bid)
    if player in round_.ordago_spent:
        raise InvalidMoveError(f"Player {player} already called their órdago this game")
    round_.ordago_caller = player
    round_.ordago_bid = bid


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
        ordago_caller=round_.ordago_caller,
        ordago_bid=round_.ordago_bid,
    )


def _score_ordago(result: RoundResult) -> dict[int, int]:
    """Coins for a round frozen by an órdago (R31-R32).

    The caller stays on board until the end, so they are in `crew`: everyone on board
    except them wins only if they miss.
    """
    on_board = [result.captain, *result.crew]
    if result.ordago_hit:
        deltas = {player: 0 for player in [*on_board, *result.deserters]}
        deltas[result.ordago_caller] = ORDAGO_HIT
        return deltas
    deltas = {player: ORDAGO_OTHERS_ON_MISS for player in on_board}
    deltas.update({player: 0 for player in result.deserters})
    deltas[result.ordago_caller] = ORDAGO_MISS
    return deltas


def score_round(result: RoundResult, treasure: bool = False) -> dict[int, int]:
    """Coins each player wins or loses this round, by position (R21-R24).

    A lone captain who fails scores like any failed mission (R24). In a treasure
    question the captain wins or loses more; everyone else scores as usual (R27).
    An órdago replaces all of that, treasure or not (R31-R33).
    """
    if result.ordago_caller is not None:
        return _score_ordago(result)
    if result.success:
        if treasure:
            captain = (
                TREASURE_LONE_CAPTAIN_SUCCESS if result.lone_captain else TREASURE_CAPTAIN_SUCCESS
            )
        else:
            captain = LONE_CAPTAIN_SUCCESS if result.lone_captain else CAPTAIN_SUCCESS
        crew = CREW_SUCCESS
        deserter = DESERTER_SUCCESS
    else:
        captain = TREASURE_CAPTAIN_FAILURE if treasure else CAPTAIN_FAILURE
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
    """Rebuild a round saved with `round_to_dict`.

    Rounds saved before the órdago existed have no órdago keys: `.get` gives them the
    "nobody called it" defaults, so games already in the database keep working.
    """
    players = [
        Player(name=player["name"], status=PlayerStatus(player["status"]))
        for player in data["players"]
    ]
    return Round(
        players=players,
        captain=data["captain"],
        current_bid=data["current_bid"],
        turn_index=data["turn_index"],
        ordago_spent=data.get("ordago_spent", []),
        ordago_caller=data.get("ordago_caller"),
        ordago_bid=data.get("ordago_bid"),
    )
