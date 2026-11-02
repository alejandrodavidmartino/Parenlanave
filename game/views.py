import random

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import engine
from .forms import NewGameForm
from .models import Game

INVALID_MOVE = "Esa jugada no está permitida."


def home(request):
    """Show the new game form and, when it is sent, create the game."""
    form = NewGameForm(request.POST or None)
    if form.is_valid():
        game = Game.start(form.cleaned_data["names"], form.cleaned_data["total_rounds"])
        return redirect("game:detail", pk=game.pk)
    return render(request, "game/home.html", {"form": form})


def game_detail(request, pk):
    game = get_object_or_404(Game, pk=pk)
    return render(request, "game/game_detail.html", _board_context(game))


@require_POST
def next_round(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if game.phase not in ("not_started", "revealed"):
        return _respond(request, game, error=INVALID_MOVE)
    try:
        game.next_round(random.Random())
    except ValueError:
        return _respond(request, game, error="No quedan rondas o preguntas.")
    return _respond(request, game)


@require_POST
def open_round(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if game.phase != "opening":
        return _respond(request, game, error=INVALID_MOVE)
    try:
        game.open_round(_read_bid(request))
    except engine.InvalidMoveError:
        return _respond(request, game, error=INVALID_MOVE)
    return _respond(request, game)


@require_POST
def play(request, pk):
    """Stay, leave or raise for the player whose turn it is (R12-R14)."""
    game = get_object_or_404(Game, pk=pk)
    if game.phase != "playing":
        return _respond(request, game, error=INVALID_MOVE)
    round_ = game.load_round()
    try:
        player = int(request.POST.get("player", ""))
        action = request.POST.get("action")
        if action == "stay":
            engine.stay(round_, player)
        elif action == "leave":
            engine.leave(round_, player)
        elif action == "raise":
            engine.raise_bid(round_, player, _read_bid(request))
        else:
            raise engine.InvalidMoveError(f"Unknown action: {action}")
    except (ValueError, engine.InvalidMoveError):
        return _respond(request, game, error=INVALID_MOVE)
    game.save_round(round_)
    return _respond(request, game)


@require_POST
def reveal(request, pk):
    """Show the real answer and give out the coins (R20-R25)."""
    game = get_object_or_404(Game, pk=pk)
    if game.phase != "round_over":
        return _respond(request, game, error=INVALID_MOVE)
    game.reveal()
    return _respond(request, game)


def _read_bid(request) -> int:
    try:
        return int(request.POST.get("bid", ""))
    except ValueError:
        raise engine.InvalidMoveError("The bid is not a whole number") from None


def _respond(request, game, error=None):
    """With HTMX, send back only the board. Without it, the whole page."""
    context = _board_context(game, error)
    if request.htmx:
        return render(request, "game/_board.html", context)
    if error:
        return render(request, "game/game_detail.html", context)
    return redirect("game:detail", pk=game.pk)


def _board_context(game, error=None):
    """Everything the board template needs, already worked out."""
    players = list(game.players.all())
    round_ = game.load_round() if game.round_state is not None else None
    context = {"game": game, "phase": game.phase, "error": error, "round": round_}

    if game.opener is not None:
        context["opener_name"] = players[game.opener].name
    if round_ is not None:
        context["captain_name"] = players[round_.captain].name
        context["turn_name"] = players[round_.turn_index].name
        context["next_bid"] = round_.current_bid + 1
    if game.round_scores is not None:
        context["result"] = game.result()
    if context["phase"] == "game_over":
        context["winners"] = [player.name for player in game.winners()]

    context["players"] = [
        {
            "name": player.name,
            "coins": player.coins,
            "captain": round_ is not None and round_.captain == player.position,
            "left": round_ is not None
            and round_.players[player.position].status == engine.PlayerStatus.LEFT,
            "score": (
                game.round_scores[player.position] if game.round_scores is not None else None
            ),
        }
        for player in players
    ]
    return context
