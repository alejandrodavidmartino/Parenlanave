import random

from django.core.validators import MinValueValidator
from django.db import models, transaction

from . import engine

# Each player picks a colour so everyone can tell them apart on screen.
# key: (name, background, text that reads well on that background).
# One colour per possible player, in the order they are given out by default.
PLAYER_COLOURS = {
    "red": ("Rojo", "#ff004d", "#fff1e8"),
    "blue": ("Azul", "#29adff", "#000000"),
    "yellow": ("Amarillo", "#ffec27", "#000000"),
    "green": ("Verde", "#00e436", "#000000"),
    "orange": ("Naranja", "#ffa300", "#000000"),
    "pink": ("Rosa", "#ff77a8", "#000000"),
    "purple": ("Morado", "#83769c", "#fff1e8"),
    "brown": ("Marrón", "#ab5236", "#fff1e8"),
}


def default_colours(count: int) -> list[str]:
    """The first `count` colours, one different colour per player."""
    return list(PLAYER_COLOURS)[:count]


def mix(colour: str, other: str, amount: float) -> str:
    """Blend two "#rrggbb" colours: `amount` of `colour`, the rest of `other`."""
    channels = [
        round(int(colour[i : i + 2], 16) * amount + int(other[i : i + 2], 16) * (1 - amount))
        for i in (1, 3, 5)
    ]
    return "#" + "".join(f"{channel:02x}" for channel in channels)


class Question(models.Model):
    """A question whose answer is a whole number, 0 or greater (R6, R9)."""

    text = models.CharField(max_length=255)
    # Big integer so answers like world population (8 000 000 000) fit.
    answer = models.PositiveBigIntegerField()
    category = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text


class Game(models.Model):
    """A game of several rounds (R2). Players are stored in `Player`."""

    total_rounds = models.PositiveSmallIntegerField(
        default=engine.DEFAULT_ROUNDS, validators=[MinValueValidator(1)]
    )
    # 0 until the first round starts, then 1, 2, 3...
    current_round = models.PositiveSmallIntegerField(default=0)
    current_question = models.ForeignKey(
        Question, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    asked_questions = models.ManyToManyField(Question, blank=True, related_name="+")
    # Position of the player who opens the current round (R7).
    opener = models.PositiveSmallIntegerField(null=True, blank=True)
    # The engine's Round saved as JSON. Empty until the opener makes their bid.
    round_state = models.JSONField(null=True, blank=True)
    # Coins each player won or lost this round, by position. Empty until the answer
    # is revealed.
    round_scores = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Game {self.pk} ({self.created_at:%d/%m/%Y %H:%M})"

    @classmethod
    def start(
        cls,
        names: list[str],
        total_rounds: int = engine.DEFAULT_ROUNDS,
        colours: list[str] | None = None,
    ) -> "Game":
        """Create a game with its players, in turn order (R1, R3).

        Without `colours`, each player gets a different one by default.
        """
        engine.check_player_count(len(names))
        colours = colours or default_colours(len(names))
        with transaction.atomic():
            game = cls.objects.create(total_rounds=total_rounds)
            Player.objects.bulk_create(
                Player(game=game, name=name, position=position, colour=colour)
                for position, (name, colour) in enumerate(zip(names, colours, strict=True))
            )
        return game

    @property
    def phase(self) -> str:
        """What the game is waiting for, so the screen knows what to show."""
        if self.current_round == 0:
            return "not_started"
        if self.round_state is None:
            return "opening"  # waiting for the opener's bid
        if not self.load_round().is_over:
            return "playing"
        if self.round_scores is None:
            return "round_over"  # waiting for the answer to be revealed
        if self.current_round >= self.total_rounds:
            return "game_over"
        return "revealed"

    def next_round(self, rng: random.Random) -> None:
        """Move on to the next round: a question not asked yet in this game (R6) and a
        random opener (R7). The round itself starts when the opener bids."""
        if self.current_round >= self.total_rounds:
            raise ValueError("The game is over")
        unasked = sorted(
            Question.objects.exclude(pk__in=self.asked_questions.all()).values_list("pk", flat=True)
        )
        if not unasked:
            raise ValueError("There are no questions left")

        with transaction.atomic():
            self.current_round += 1
            self.current_question_id = rng.choice(unasked)
            self.opener = engine.choose_opener(self.players.count(), rng)
            self.round_state = None
            self.round_scores = None
            self.save()
            self.asked_questions.add(self.current_question_id)

    def open_round(self, opening_bid: int) -> None:
        """The opener makes the opening bid and the round starts (R8)."""
        names = [player.name for player in self.players.all()]
        self.save_round(engine.start_round(names, self.opener, opening_bid))

    def result(self) -> engine.RoundResult:
        """What happened in the finished round, compared with the real answer (R20)."""
        return engine.finish_round(self.load_round(), self.current_question.answer)

    def reveal(self) -> None:
        """Reveal the answer and give or take each player's coins (R21-R25)."""
        deltas = engine.score_round(self.result())
        players = list(self.players.all())
        new_coins = engine.apply_scores([player.coins for player in players], deltas)
        for player, coins in zip(players, new_coins, strict=True):
            player.coins = coins

        with transaction.atomic():
            Player.objects.bulk_update(players, ["coins"])
            self.round_scores = [deltas[player.position] for player in players]
            self.save(update_fields=["round_scores"])

    def winners(self) -> list["Player"]:
        """The players with the most coins. Ties share the win (R4)."""
        players = list(self.players.all())
        return [players[i] for i in engine.winners([player.coins for player in players])]

    def load_round(self) -> engine.Round:
        """The current round, rebuilt from the database."""
        return engine.round_from_dict(self.round_state)

    def save_round(self, round_: engine.Round) -> None:
        """Store the current round in the database."""
        self.round_state = engine.round_to_dict(round_)
        self.save(update_fields=["round_state"])


class Player(models.Model):
    """A player in a game. `position` is their place in the turn order (R10)."""

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=30)
    position = models.PositiveSmallIntegerField()
    coins = models.PositiveIntegerField(default=engine.STARTING_COINS)
    colour = models.CharField(
        max_length=10,
        choices=[(key, name) for key, (name, _, _) in PLAYER_COLOURS.items()],
        default="red",
    )

    class Meta:
        ordering = ["game", "position"]
        constraints = [
            models.UniqueConstraint(fields=["game", "position"], name="unique_position_per_game"),
        ]

    def __str__(self):
        return self.name

    @property
    def background(self) -> str:
        """The player's colour, ready for CSS."""
        return PLAYER_COLOURS[self.colour][1]

    @property
    def text_colour(self) -> str:
        """A text colour that reads well on the player's colour."""
        return PLAYER_COLOURS[self.colour][2]

    @property
    def muted_background(self) -> str:
        """The player's colour toned down with the game's night blue, for big areas
        like the "pass the phone" screen, where the bright colour hurts the eyes."""
        return mix(self.background, "#1d2b53", 0.4)
