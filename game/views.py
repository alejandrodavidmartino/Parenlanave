from django.shortcuts import get_object_or_404, redirect, render

from .forms import NewGameForm
from .models import Game


def home(request):
    """Show the new game form and, when it is sent, create the game."""
    form = NewGameForm(request.POST or None)
    if form.is_valid():
        game = Game.start(form.cleaned_data["names"], form.cleaned_data["total_rounds"])
        return redirect("game:detail", pk=game.pk)
    return render(request, "game/home.html", {"form": form})


def game_detail(request, pk):
    game = get_object_or_404(Game, pk=pk)
    return render(request, "game/game_detail.html", {"game": game})
