from django import forms

from . import engine
from .models import PLAYER_COLOURS, default_colours

INPUT_CLASSES = "input-px"


class NewGameForm(forms.Form):
    """Players' names and colours (one row per possible player) and number of rounds."""

    total_rounds = forms.IntegerField(
        label="Rondas",
        min_value=1,
        max_value=20,
        initial=engine.DEFAULT_ROUNDS,
        widget=forms.NumberInput(attrs={"class": INPUT_CLASSES}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # One optional row per possible player; rows without a name are ignored (R1).
        # The colour is a hidden field: the colour button next to the name changes it.
        colours = default_colours(engine.MAX_PLAYERS)
        for number, colour in enumerate(colours, start=1):
            self.fields[f"player_{number}"] = forms.CharField(
                label=f"Jugador {number}",
                max_length=30,
                required=False,
                widget=forms.TextInput(
                    attrs={"class": INPUT_CLASSES, "placeholder": f"Jugador {number}"}
                ),
            )
            self.fields[f"colour_{number}"] = forms.ChoiceField(
                choices=[(key, name) for key, (name, _, _) in PLAYER_COLOURS.items()],
                initial=colour,
                required=False,
                widget=forms.HiddenInput,
            )

    def player_rows(self):
        """Each player's name box, colour field and colour, for the template."""
        rows = []
        for number, default in enumerate(default_colours(engine.MAX_PLAYERS), start=1):
            colour = self[f"colour_{number}"]
            key = colour.value() if colour.value() in PLAYER_COLOURS else default
            rows.append(
                {
                    "name": self[f"player_{number}"],
                    "colour": colour,
                    "background": PLAYER_COLOURS[key][1],
                    "text_colour": PLAYER_COLOURS[key][2],
                }
            )
        return rows

    def visible_players(self):
        """How many name boxes to show: the minimum (R1), or up to the last one filled in,
        so names typed before an error never get hidden."""
        filled = [
            number
            for number, row in enumerate(self.player_rows(), start=1)
            if (row["name"].value() or "").strip()
        ]
        return max([engine.MIN_PLAYERS, *filled])

    def clean(self):
        cleaned_data = super().clean()
        # A row without a colour (old form, no JavaScript...) keeps its default one.
        defaults = default_colours(engine.MAX_PLAYERS)
        players = [
            (
                cleaned_data[f"player_{number}"].strip(),
                cleaned_data.get(f"colour_{number}") or defaults[number - 1],
            )
            for number in range(1, engine.MAX_PLAYERS + 1)
            if cleaned_data.get(f"player_{number}", "").strip()
        ]
        try:
            engine.check_player_count(len(players))
        except ValueError:
            raise forms.ValidationError(
                f"Hacen falta entre {engine.MIN_PLAYERS} y {engine.MAX_PLAYERS} jugadores."
            ) from None

        colours = [colour for _, colour in players]
        if len(set(colours)) != len(colours):
            raise forms.ValidationError("Cada jugador necesita un color distinto.")

        cleaned_data["names"] = [name for name, _ in players]
        cleaned_data["colours"] = colours
        return cleaned_data
