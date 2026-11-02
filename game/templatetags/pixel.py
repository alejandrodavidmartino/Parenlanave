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
    "P": "#ff004d",
    "V": "#00e436",
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
    # Title screen: the pirate on the dock and the ship far away on the horizon.
    "pirate": [
        "...KKKKKK...",
        "..KKKKKKKK..",
        "..KKKWWKKK..",
        "KKKKKKKKKKKK",
        "...SSSSSS...",
        "...KKSSKSS..",
        "...SSSSSS...",
        "...RRRRRR...",
        "....RRRR....",
        "..PPPPPPPP..",
        ".PPPPYYPPPP.",
        "SPPPPPPPPPPS",
        "SPPPPYYPPPPS",
        ".PPPPPPPPPP.",
        "..KKKKKKKK..",
        "..KKKYYKKK..",
        "..DDDDDDDD..",
        "..DDD..DDD..",
        "..DDD..DDD..",
        "..DDD...R...",
        "..KKK...R...",
        ".KKKK...R...",
    ],
    # Sits on the pirate's shoulder, looking away from him.
    "parrot": [
        "..VVV.",
        ".YVKV.",
        "YYVVV.",
        "..VVVV",
        "..VPVV",
        "...VPV",
        "...YY.",
    ],
    "ship_far": [
        "......K.......",
        ".....KK...K...",
        "....KKK..KK...",
        "...KKKK.KKK...",
        "..KKKKK.KKKK..",
        "......K....K..",
        "KKKKKKKKKKKKKK",
        ".KKKKKKKKKKKK.",
        "..KKKKKKKKKK..",
    ],
}

SCENE_COLOURS = {
    "night": "#1d2b53",
    "plum": "#7e2553",
    "red": "#ff004d",
    "orange": "#ffa300",
    "gold": "#ffec27",
    "cream": "#fff1e8",
    "sea": "#29adff",
    "wood": "#ab5236",
    "black": "#000000",
}


def _rects(rows, dx=0, dy=0):
    """SVG rectangles for a sprite, moved `dx`, `dy` pixels."""
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
                rects.append(_rect(x + dx, y + dy, run, 1, colour))
            x += run
    return rects


def _rect(x, y, width, height, colour):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{colour}"/>'


@register.simple_tag
def sprite(name, scale=4, label=""):
    """Draw a sprite `scale` screen pixels per sprite pixel.

    Usage: {% sprite "anchor" 3 "Capitán" %}. Without a label, screen readers skip it.
    """
    rows = SPRITES[name]
    width, height = len(rows[0]), len(rows)
    a11y = f'role="img" aria-label="{escape(label)}"' if label else 'aria-hidden="true"'
    return mark_safe(
        f'<svg width="{width * scale}" height="{height * scale}" viewBox="0 0 {width} {height}" '
        f'shape-rendering="crispEdges" class="inline-block align-middle" {a11y}>'
        f"{''.join(_rects(rows))}</svg>"
    )


@register.simple_tag
def title_scene():
    """The title screen picture: a pirate on a wooden dock at sunset, a ship far away.

    It is 120 x 90 pixels, stretched to the width of the screen.
    """
    c = SCENE_COLOURS
    width, height, horizon = 120, 90, 48
    parts = []

    # Sky: bands of colour from night (top) to the setting sun (bottom)...
    bands = [(0, "night"), (10, "plum"), (19, "red"), (29, "orange"), (39, "gold")]
    for (top, colour), (bottom, _) in zip(bands, [*bands[1:], (horizon, None)], strict=True):
        parts.append(_rect(0, top, width, bottom - top, c[colour]))
    # ...blended with dithering: a checkerboard row on each side of every border.
    for (_, above), (border, below) in zip(bands, bands[1:], strict=False):
        parts.extend(_rect(x, border - 1, 1, 1, c[below]) for x in range(0, width, 2))
        parts.extend(_rect(x, border, 1, 1, c[above]) for x in range(1, width, 2))
    for x, y in ((8, 3), (27, 8), (44, 2), (63, 6), (97, 4), (112, 9), (76, 10)):
        parts.append(_rect(x, y, 1, 1, c["cream"]))

    # Half of the sun, sinking behind the horizon, with a golden glow around it.
    sun_x = 84
    for radius, colour in ((12, "gold"), (9, "cream")):
        for dy in range(1, radius + 1):
            half = round((radius**2 - (dy - 0.5) ** 2) ** 0.5)
            parts.append(_rect(sun_x - half, horizon - dy, half * 2, 1, c[colour]))

    # Sea, with the sun's reflection and a few waves.
    parts.append(_rect(0, horizon, width, height - horizon, c["night"]))
    for y, half in ((49, 9), (51, 7), (53, 6), (55, 4), (57, 3), (59, 2)):
        parts.append(_rect(sun_x - half, y, half * 2, 1, c["orange"] if y < 54 else c["gold"]))
    for x, y in ((6, 52), (30, 55), (50, 51), (104, 54), (12, 60), (98, 61)):
        parts.append(_rect(x, y, 5, 1, c["sea"]))

    # The ship on the horizon. The <g> lets CSS make it bob up and down.
    parts.append('<g class="animate-bob">')
    parts.extend(_rects(SPRITES["ship_far"], dx=20, dy=horizon - 8))
    parts.append("</g>")

    # The wooden dock in front: top boards, front edge and posts going into the water.
    dock_top, dock_end = 68, 84
    parts.append(_rect(0, dock_top, dock_end, 5, c["wood"]))
    for x in range(8, dock_end, 9):
        parts.append(_rect(x, dock_top, 1, 5, c["black"]))
    parts.append(_rect(0, dock_top + 5, dock_end, 2, c["black"]))
    for x in (4, 30, 56, dock_end - 4):
        parts.append(_rect(x, dock_top + 7, 3, height - dock_top - 7, c["wood"]))
        parts.append(_rect(x + 2, dock_top + 7, 1, height - dock_top - 7, c["black"]))

    # The pirate, standing on the dock and looking out to sea, with his parrot sitting
    # on his shoulder (row 9 of the pirate sprite).
    pirate = SPRITES["pirate"]
    pirate_x, pirate_y = 58, dock_top - len(pirate)
    parts.extend(_rects(pirate, dx=pirate_x, dy=pirate_y))
    parrot = SPRITES["parrot"]
    parts.extend(_rects(parrot, dx=pirate_x - 2, dy=pirate_y + 9 - len(parrot)))

    return mark_safe(
        f'<svg viewBox="0 0 {width} {height}" shape-rendering="crispEdges" '
        f'class="block h-auto w-full" role="img" '
        f'aria-label="Un pirata en un muelle de madera mira un barco al atardecer">'
        f"{''.join(parts)}</svg>"
    )
