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
    # Figures for the reveal scene, with a black outline so each one stands out.
    # "C" is the player's colour: a whole shirt of it, easy to spot from far away.
    "deck_sailor": [
        ".KKKKK.",
        "KWWWWWK",
        "KCCCCCK",
        "KSSSSSK",
        "KSKSKSK",
        ".KSSSK.",
        "KCCCCCK",
        "SCCCCCS",
        "KCCCCCK",
        ".KDKDK.",
        ".KK.KK.",
    ],
    "deck_captain": [
        "KKKKKKK",
        "KKYYYKK",
        ".KKKKK.",
        "KSSSSSK",
        "KSKSKSK",
        ".KSSSK.",
        "KCCCCCK",
        "SCYCYCS",
        "KCCCCCK",
        ".KDKDK.",
        ".KK.KK.",
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


# Colours of the reveal scene: a harbour at night, nothing like the sunset title screen.
NIGHT_COLOURS = {
    "sky_top": "#0b1230",
    "sky": "#1d2b53",
    "sea": "#0f2f55",
    "wave": "#29adff",
    "foam": "#83d6ff",
    "moon": "#fff1e8",
    "crater": "#c2c3c7",
    "land": "#000000",
    "lamp": "#ffec27",
    "stripe": "#ff004d",
    "wood": "#ab5236",
    "gold": "#ffec27",
    "sail": "#fff1e8",
    "flag": "#ff004d",
    "black": "#000000",
}


@register.simple_tag
def voyage_scene(result, players):
    """The reveal animation: a harbour at night, 96 x 56 pixels, seen up close.

    The captain and crew stand on the ship, the deserters on the dock, each in their
    colour. If the mission succeeds the ship sails away and leaves the deserters behind;
    if it fails it blows up and sinks. `result` is the engine's RoundResult and `players`
    the board's player list (in turn order, each with its "background" colour).
    """
    c = NIGHT_COLOURS
    width, height, horizon, deck = 96, 56, 30, 40
    parts = []

    # Night sky, dithered from almost black at the top to night blue.
    parts.append(_rect(0, 0, width, horizon, c["sky"]))
    parts.append(_rect(0, 0, width, 13, c["sky_top"]))
    parts.extend(_rect(x, 13, 1, 1, c["sky_top"]) for x in range(1, width, 2))
    parts.extend(_rect(x, 12, 1, 1, c["sky"]) for x in range(0, width, 2))
    # Stars; some of them twinkle, each at its own pace.
    for x, y in ((4, 3), (15, 8), (26, 2), (38, 6), (50, 3), (58, 11), (88, 4), (93, 12)):
        parts.append(_rect(x, y, 1, 1, c["moon"]))
    for index, (x, y) in enumerate(((10, 14), (33, 11), (46, 16), (80, 15))):
        delay = f"{index * 0.3:.1f}"
        parts.append(f'<g class="animate-twinkle" style="animation-delay: {delay}s">')
        parts.append(_rect(x, y, 1, 1, c["moon"]))
        parts.append("</g>")

    # The moon, with a few craters.
    moon_x, moon_y, radius = 70, 9, 5
    for dy in range(-radius, radius + 1):
        half = round((radius**2 - dy**2) ** 0.5)
        parts.append(_rect(moon_x - half, moon_y + dy, half * 2 + 1, 1, c["moon"]))
    for x, y in ((-2, -1), (1, 2), (2, -2)):
        parts.append(_rect(moon_x + x, moon_y + y, 1, 1, c["crater"]))

    # A lighthouse on a dark headland, its lamp blinking.
    parts.append(_rect(80, horizon - 3, 16, 3, c["land"]))
    parts.append(_rect(84, horizon - 5, 12, 2, c["land"]))
    for row in range(8):
        stripe = c["stripe"] if row % 4 < 2 else c["moon"]
        parts.append(_rect(88, horizon - 13 + row, 3, 1, stripe))
    parts.append(_rect(87, horizon - 16, 5, 3, c["black"]))
    parts.append('<g class="animate-twinkle">')
    parts.append(_rect(88, horizon - 15, 3, 1, c["lamp"]))
    parts.append(_rect(76, horizon - 15, 11, 1, c["lamp"]))
    parts.append("</g>")

    # The sea, the moon's reflection and waves that drift sideways.
    parts.append(_rect(0, horizon, width, height - horizon, c["sea"]))
    parts.append('<g class="animate-twinkle">')
    for y, half in ((31, 4), (33, 3), (35, 4), (37, 2), (39, 3)):
        parts.append(_rect(moon_x - half, y, half * 2, 1, c["moon"]))
    parts.append("</g>")
    parts.append('<g class="animate-waves">')
    for y, offset, colour in ((32, 0, "wave"), (36, 4, "foam"), (46, 2, "wave"), (51, 6, "foam")):
        parts.extend(_rect(x, y, 3, 1, c[colour]) for x in range(offset, width - 2, 9))
    parts.append("</g>")

    # The dock on the left, just long enough for the deserters standing on it.
    deserters = [players[position] for position in result.deserters]
    dock_end = max(12, 3 + len(deserters) * 6)
    parts.append(_rect(0, deck, dock_end, 3, c["wood"]))
    parts.append(_rect(0, deck + 3, dock_end, 1, c["black"]))
    for x in range(2, dock_end - 1, 8):
        parts.append(_rect(x, deck + 4, 2, height - deck - 4, c["wood"]))
    # A lone captain who sinks makes the deserters jump for joy: they were right.
    cheering = result.lone_captain and not result.success
    for index, player in enumerate(deserters):
        if cheering:
            delay = f"{1.5 + index * 0.1:.1f}"
            parts.append(f'<g class="animate-cheer" style="animation-delay: {delay}s">')
        parts.extend(_figure(player, "deck_sailor", 1 + index * 6, deck - 11))
        if cheering:
            parts.append("</g>")

    # The ship moored next to the dock, with the captain and crew on deck. The outer
    # <g> rocks it while everyone waits; the inner one sails it away or sinks it.
    ship_x, ship_width = dock_end + 2, 44
    animation = "animate-sail-away sail-away" if result.success else "animate-sink sink"
    parts.append(f'<g class="animate-rock"><g class="{animation}">')
    parts.extend(_ship(ship_x, deck, ship_width))
    on_board = [result.captain, *result.crew]
    spacing = min(7, (ship_width - 8) // len(on_board))
    for index, position in enumerate(on_board):
        kind = "deck_captain" if position == result.captain else "deck_sailor"
        parts.extend(_figure(players[position], kind, ship_x + 3 + index * spacing, deck - 11))
    if result.lone_captain and result.success:
        # A lone captain who makes it keeps all the loot: a sparkling treasure chest.
        chest_x, chest_y = ship_x + 12, deck - 6
        parts.append('<g class="treasure">')
        parts.extend(_rects(SPRITES["chest"], dx=chest_x, dy=chest_y))
        parts.append('<g class="animate-twinkle">')
        for x, y in ((1, -3), (6, -2), (3, -5)):
            parts.append(_rect(chest_x + x, chest_y + y, 1, 1, c["moon"]))
        parts.append("</g></g>")
    parts.append("</g></g>")

    if not result.success:
        # The explosion, three times bigger than its sprite so it covers the ship.
        boom_x, boom_y = ship_x + ship_width // 2 - 15, deck - 26
        parts.append(
            f'<g class="animate-boom"><g transform="translate({boom_x} {boom_y}) scale(3)">'
        )
        parts.extend(_rects(SPRITES["boom"]))
        parts.append("</g></g>")
        # Water in front of the ship, so it disappears below the surface as it sinks.
        parts.append(_rect(ship_x - 2, deck + 4, ship_width + 4, height - deck - 4, c["sea"]))

    label = (
        "El barco zarpa de noche con la tripulación y deja a los desertores en el muelle"
        if result.success
        else "El barco explota y se hunde con la tripulación"
    )
    return mark_safe(
        f'<svg viewBox="0 0 {width} {height}" shape-rendering="crispEdges" '
        f'class="block h-auto w-full overflow-hidden" role="img" aria-label="{label}">'
        f"{''.join(parts)}</svg>"
    )


def _figure(player, kind, x, y):
    """A crew member drawn in the player's colour."""
    palette = {**PALETTE, "C": escape(player["background"])}
    return _rects(SPRITES[kind], dx=x, dy=y, palette=palette)


def _ship(x, deck, width):
    """A sailing ship: hull with a gold stripe and portholes, two sails and a flag."""
    c = NIGHT_COLOURS
    mast = x + width * 11 // 20
    parts = [
        _rect(mast, deck - 27, 1, 27, c["black"]),
        _rect(mast + 1, deck - 27, 5, 3, c["flag"]),
    ]
    for row in range(20):  # main sail behind the mast, widening downwards
        parts.append(_rect(mast + 1, deck - 23 + row, 2 + row * 14 // 20, 1, c["sail"]))
    for row in range(14):  # smaller front sail
        sail_width = 1 + row * 10 // 14
        parts.append(_rect(mast - sail_width, deck - 16 + row, sail_width, 1, c["sail"]))
    parts.append(_rect(x - 1, deck, width + 2, 1, c["black"]))  # deck rail
    for row in range(6):  # hull, narrower towards the keel, with a gold stripe
        colour = c["gold"] if row == 1 else c["wood"]
        parts.append(_rect(x + row, deck + 1 + row, width - row * 2, 1, colour))
        parts.append(_rect(x + row, deck + 1 + row, 1, 1, c["black"]))
        parts.append(_rect(x + width - 1 - row, deck + 1 + row, 1, 1, c["black"]))
    for porthole in range(x + 6, x + width - 6, 7):
        parts.append(_rect(porthole, deck + 3, 2, 1, c["black"]))
    parts.append(_rect(x + 6, deck + 7, width - 12, 1, c["black"]))  # keel
    return parts
