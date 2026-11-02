from django import forms

from . import engine

INPUT_CLASSES = "input-px"


class NewGameForm(forms.Form):
    """Players' names (one box per possible player) and number of rounds."""

    total_rounds = forms.IntegerField(
        label="Rondas",
        min_value=1,
        max_value=20,
        initial=engine.DEFAULT_ROUNDS,
        widget=forms.NumberInput(attrs={"class": INPUT_CLASSES}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # One optional box per possible player; empty boxes are ignored (R1).
        for number in range(1, engine.MAX_PLAYERS + 1):
            self.fields[f"player_{number}"] = forms.CharField(
                label=f"Jugador {number}",
                max_length=30,
                required=False,
                widget=forms.TextInput(
                    attrs={"class": INPUT_CLASSES, "placeholder": f"Jugador {number}"}
                ),
            )

    def player_fields(self):
        """The name boxes, so the template can show them apart from the rounds box."""
        return [self[name] for name in self.fields if name.startswith("player_")]

    def clean(self):
        cleaned_data = super().clean()
        names = [
            cleaned_data[name].strip()
            for name in self.fields
            if name.startswith("player_") and cleaned_data.get(name, "").strip()
        ]
        try:
            engine.check_player_count(len(names))
        except ValueError:
            raise forms.ValidationError(
                f"Hacen falta entre {engine.MIN_PLAYERS} y {engine.MAX_PLAYERS} jugadores."
            ) from None
        cleaned_data["names"] = names
        return cleaned_data
