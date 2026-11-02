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
    # A ship's crew member for the "pass the phone" screen. "C" is the player's colour:
    # the band on the cap and the stripes on the shirt.
    "sailor": [
        "...WWWWWW...",
        "..WWWWWWWW..",
        "..CCCCCCCC..",
        "...SSSSSS...",
        "...SKSSKS...",
        "...SSSSSS...",
        "...SSKKSS...",
        "....SSSS....",
        "..CCCCCCCC..",
        ".WWWWWWWWWW.",
        "SCCCCCCCCCCS",
        "SWWWWWWWWWWS",
        ".CCCCCCCCCC.",
        "..DDDDDDDD..",
        "..DDD..DDD..",
        "..KKK..KKK..",
    ],
    # Small figures for the reveal scene. "C" is the player's colour.
    "mini_sailor": [
        ".WWW.",
        ".CCC.",
        ".SSS.",
        "CCCCC",
        "SWWWS",
        ".CCC.",
        ".D.D.",
        ".K.K.",
    ],
    "mini_captain": [
        "KKKKK",
        ".KYK.",
        ".SSS.",
        "CCCCC",
        "SWWWS",
        ".CCC.",
        ".D.D.",
        ".K.K.",
    ],
    # The lone captain's loot.
    "chest": [
        ".KKKKKK.",
        "KRYRRYRK",
        "KKKYYKKK",
        "KRRYYRRK",
        "KRYRRYRK",
        "KKKKKKKK",
    ],
    "boom": [
        "...Y...Y..",
        ".Y..O.O..Y",
        "...OOPOO..",
        "Y.OPPYPPO.",
        "..OPYWYPO.",
        ".OPYWWYPOY",
        "..OPYYPO..",
        "Y..OPPO..Y",
        "...O..O...",
        ".Y...Y....",
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


def _rects(rows, dx=0, dy=0, palette=PALETTE):
    """SVG rectangles for a sprite, moved `dx`, `dy` pixels."""
    rects = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            colour = palette.get(row[x])
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
def sprite(name, scale=4, label="", colour="#ff004d"):
    """Draw a sprite `scale` screen pixels per sprite pixel.

    Usage: {% sprite "anchor" 3 "Capitán" %}. Without a label, screen readers skip it.
    `colour` paints the "C" pixels, for sprites that change colour (the sailor).
    """
    rows = SPRITES[name]
    palette = {**PALETTE, "C": escape(colour)}
    width, height = len(rows[0]), len(rows)
    a11y = f'role="img" aria-label="{escape(label)}"' if label else 'aria-hidden="true"'
    return mark_safe(
        f'<svg width="{width * scale}" height="{height * scale}" viewBox="0 0 {width} {height}" '
        f'shape-rendering="crispEdges" class="inline-block align-middle" {a11y}>'
        f"{''.join(_rects(rows, palette=palette))}</svg>"
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


@register.simple_tag
def voyage_scene(result, players):
    """The reveal animation, 120 x 60 pixels.

    The captain and crew stand on the ship, the deserters on the dock. If the mission
    succeeds the ship sails away and leaves the deserters behind; if it fails it blows
    up and sinks. `result` is the engine's RoundResult and `players` the board's player
    list (in turn order, each with its "background" colour).
    """
    c = SCENE_COLOURS
    width, height, waterline = 120, 60, 42
    parts = []

    # Sunset sky and sea, like the title screen but shorter.
    bands = [(0, "night"), (8, "plum"), (16, "red"), (25, "orange"), (34, "gold")]
    for (top, colour), (bottom, _) in zip(bands, [*bands[1:], (waterline, None)], strict=True):
        parts.append(_rect(0, top, width, bottom - top, c[colour]))
    for (_, above), (border, below) in zip(bands, bands[1:], strict=False):
        parts.extend(_rect(x, border - 1, 1, 1, c[below]) for x in range(0, width, 2))
        parts.extend(_rect(x, border, 1, 1, c[above]) for x in range(1, width, 2))
    parts.append(_rect(0, waterline, width, height - waterline, c["night"]))

    # The dock on the left, with the deserters standing on it.
    dock_end = 44
    parts.append(_rect(0, waterline - 2, dock_end, 3, c["wood"]))
    parts.append(_rect(0, waterline + 1, dock_end, 1, c["black"]))
    for x in (3, 20, dock_end - 4):
        parts.append(_rect(x, waterline + 2, 2, height - waterline - 2, c["wood"]))
    deserters = [players[position] for position in result.deserters]
    # A lone captain who sinks makes the deserters jump for joy: they were right.
    cheering = result.lone_captain and not result.success
    for index, player in enumerate(deserters):
        if cheering:
            parts.append(
                f'<g class="animate-cheer" style="animation-delay: {1.5 + index * 0.1:.1f}s">'
            )
        parts.extend(_mini(player, "mini_sailor", 2 + index * 6, waterline - 10))
        if cheering:
            parts.append("</g>")

    # The ship moored next to the dock, with the captain and crew on deck. Everything
    # inside the <g> moves together: it sails away or sinks.
    ship_x, deck = 48, waterline - 4
    animation = "animate-sail-away sail-away" if result.success else "animate-sink sink"
    parts.append(f'<g class="{animation}">')
    parts.extend(_ship(ship_x, deck))
    on_board = [result.captain, *result.crew]
    spacing = min(6, 26 // len(on_board))
    for index, position in enumerate(on_board):
        kind = "mini_captain" if position == result.captain else "mini_sailor"
        parts.extend(_mini(players[position], kind, ship_x + 2 + index * spacing, deck - 8))
    if result.lone_captain and result.success:
        # A lone captain who makes it keeps all the loot: a sparkling treasure chest.
        chest_x = ship_x + 9
        parts.extend(_rects(SPRITES["chest"], dx=chest_x, dy=deck - 6))
        parts.append('<g class="animate-twinkle">')
        for x, y in ((1, -3), (6, -2), (3, -5)):
            parts.append(_rect(chest_x + x, deck - 6 + y, 1, 1, c["cream"]))
        parts.append("</g>")
    parts.append("</g>")

    if not result.success:
        # The explosion is drawn twice as big (scale) so it covers the whole ship.
        parts.append(
            f'<g class="animate-boom"><g transform="translate({ship_x + 5} {deck - 16}) scale(2)">'
        )
        parts.extend(_rects(SPRITES["boom"]))
        parts.append("</g></g>")
        # Water in front of the ship, so it disappears below the surface as it sinks.
        parts.append(_rect(ship_x - 4, waterline + 1, 40, height - waterline - 1, c["night"]))

    label = (
        "El barco zarpa con la tripulación y deja a los desertores en el muelle"
        if result.success
        else "El barco explota y se hunde con la tripulación"
    )
    return mark_safe(
        f'<svg viewBox="0 0 {width} {height}" shape-rendering="crispEdges" '
        f'class="block h-auto w-full overflow-hidden" role="img" aria-label="{label}">'
        f"{''.join(parts)}</svg>"
    )


def _mini(player, kind, x, y):
    """A small figure in the player's colour."""
    palette = {**PALETTE, "C": escape(player["background"])}
    return _rects(SPRITES[kind], dx=x, dy=y, palette=palette)


def _ship(x, deck):
    """A small sailing ship: mast, two sails and a flag over a wooden hull."""
    c = SCENE_COLOURS
    parts = [_rect(x + 14, deck - 18, 1, 18, c["black"]), _rect(x + 15, deck - 18, 4, 2, c["red"])]
    for row in range(12):  # main sail, getting wider towards the bottom
        parts.append(_rect(x + 15, deck - 15 + row, 1 + row * 9 // 12, 1, c["cream"]))
    for row in range(8):  # small sail at the front
        parts.append(_rect(x + 13 - row * 6 // 8, deck - 10 + row, 1 + row * 6 // 8, 1, c["cream"]))
    parts.append(_rect(x, deck, 30, 1, c["black"]))  # deck
    for row, inset in enumerate((0, 1, 2, 3)):  # hull, narrower at the bottom
        parts.append(_rect(x + inset, deck + 1 + row, 30 - inset * 2, 1, c["wood"]))
        parts.append(_rect(x + inset, deck + 1 + row, 1, 1, c["black"]))
        parts.append(_rect(x + 29 - inset, deck + 1 + row, 1, 1, c["black"]))
    parts.append(_rect(x + 4, deck + 5, 22, 1, c["black"]))  # keel
    return parts
