"""Pixel art sprites drawn as SVG, so they stay sharp at any size."""

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# One letter per colour; "." is transparent.
PALETTE = {
    "K": "#000000",
    "Y": "#ffec27",
    "O": "#ffa300",
    "W": "#fff1e8",
    "G": "#c2c3c7",
    "B": "#29adff",
    "D": "#5f574f",
    "R": "#ab5236",
    "S": "#ffccaa",
}

# Each sprite is a list of rows, one character per pixel.
SPRITES = {
    "anchor": [
        "....K....",
        "...K.K...",
        "....K....",
        ".KKKKKKK.",
        "....K....",
        "K...K...K",
        "KK..K..KK",
        ".KK.K.KK.",
        "..KKKKK..",
    ],
    "coin": [
        "..KKKK..",
        ".KYYYYK.",
        "KYYOYYYK",
        "KYYOYYYK",
        "KYYOYYYK",
        "KYYYYYOK",
        ".KYYYOK.",
        "..KKKK..",
    ],
    "trophy": [
        "KKKKKKKKK",
        "KYYYYYYYK",
        "KYKYYYKYK",
        ".KYYYYYK.",
        "..KYYYK..",
        "...KYK...",
        "...KYK...",
        "..KYYYK..",
        ".KKKKKKK.",
    ],
    "phone": [
        ".KKKKK.",
        "KBBBBBK",
        "KBWBBBK",
        "KBBBBBK",
        "KBBBBBK",
        "KBBBBBK",
        "KDDDDDK",
        ".KKKKK.",
    ],
    "face": [
        "..RRRRR..",
        ".RRRRRRR.",
        "RRSSSSSRR",
        "RSSKSKSSR",
        "RSSSSSSSR",
        "RSSKKKSSR",
        ".SSSSSSS.",
        "..SSSSS..",
    ],
    "skull": [
        "..KKKKK..",
        ".KWWWWWK.",
        "KWWWWWWWK",
        "KWKKWKKWK",
        "KWKKWKKWK",
        "KWWWKWWWK",
        ".KWWWWWK.",
        "..KWKWK..",
        "..KKKKK..",
    ],
    "ship": [
        "......K.........",
        "......KW........",
        "......KWW.......",
        "......KWWW......",
        "......KWWWW.....",
        "......KWWWWW....",
        "......K.........",
        "KKKKKKKKKKKKKKKK",
        ".KRRRRRRRRRRRRK.",
        "..KRRRRRRRRRRK..",
        "BB.BBB.BBB.BBB.B",
    ],
}


@register.simple_tag
def sprite(name, scale=4, label=""):
    """Draw a sprite `scale` screen pixels per sprite pixel.

    Usage: {% sprite "anchor" 3 "Capitán" %}. Without a label, screen readers skip it.
    """
    rows = SPRITES[name]
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            colour = PALETTE.get(row[x])
            run = 1
            # Join pixels of the same colour in a row into one rectangle.
            while x + run < len(row) and row[x + run] == row[x]:
                run += 1
            if colour:
                rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="{colour}"/>')
            x += run

    width, height = len(rows[0]), len(rows)
    a11y = f'role="img" aria-label="{escape(label)}"' if label else 'aria-hidden="true"'
    return mark_safe(
        f'<svg width="{width * scale}" height="{height * scale}" viewBox="0 0 {width} {height}" '
        f'shape-rendering="crispEdges" class="inline-block align-middle" {a11y}>'
        f"{''.join(rects)}</svg>"
    )
