import re

from django.template import Context, Template

from game.engine import RoundResult
from game.templatetags.pixel import SPRITES, sprite, title_scene, voyage_scene


def render(text):
    return Template("{% load pixel %}" + text).render(Context())


def test_sprite_size_is_its_pixels_times_the_scale():
    svg = sprite("coin", scale=3)

    assert 'width="24" height="24"' in svg  # 8x8 pixels


def test_pixels_of_the_same_colour_in_a_row_are_joined():
    svg = sprite("coin")

    # First row "..KKKK..": one black rectangle 4 pixels wide.
    assert '<rect x="2" y="0" width="4" height="1" fill="#000000"/>' in svg


def test_transparent_pixels_are_not_drawn():
    svg = sprite("anchor")

    assert 'x="0" y="0"' not in svg


def test_sprite_without_label_is_hidden_from_screen_readers():
    assert 'aria-hidden="true"' in render('{% sprite "ship" %}')


def test_sprite_with_label_is_announced_and_escaped():
    html = render('{% sprite "anchor" 2 "<Capitán>" %}')

    assert 'role="img" aria-label="&lt;Capitán&gt;"' in html


def test_every_sprite_is_a_rectangle():
    for name, rows in SPRITES.items():
        assert len({len(row) for row in rows}) == 1, name


def test_title_scene_fits_its_120_by_90_canvas():
    svg = title_scene()

    assert 'viewBox="0 0 120 90"' in svg
    assert 'aria-label="Un pirata en un muelle de madera mira un barco al atardecer"' in svg
    assert 'class="animate-bob"' in svg  # the ship bobs on the sea


def test_title_scene_draws_everything_inside_the_canvas():
    svg = title_scene()

    for x, y, width, height in re.findall(
        r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)"', svg
    ):
        assert int(x) + int(width) <= 120
        assert int(y) + int(height) <= 90


def test_sprite_colour_paints_the_c_pixels():
    svg = sprite("sailor", colour="#00e436")

    assert 'fill="#00e436"' in svg


# Reveal scene.


def players(*colours):
    return [{"background": colour} for colour in colours]


def test_successful_voyage_sails_away_with_the_crew_on_board():
    result = RoundResult(captain=0, crew=[1], deserters=[2], bid=10, answer=20)

    svg = voyage_scene(result, players("#ff004d", "#29adff", "#00e436"))

    assert "zarpa" in svg
    ship = svg[svg.index('<g class="animate-sail-away') : svg.index("</g>")]
    assert 'fill="#ff004d"' in ship and 'fill="#29adff"' in ship  # captain and crew
    assert 'fill="#00e436"' not in ship  # the deserter stays on the dock
    assert 'fill="#00e436"' in svg


def test_failed_voyage_blows_up_and_sinks():
    result = RoundResult(captain=0, crew=[], deserters=[1, 2], bid=99, answer=20)

    svg = voyage_scene(result, players("#ff004d", "#29adff", "#00e436"))

    assert 'class="animate-sink sink"' in svg
    assert 'class="animate-boom"' in svg
    assert "se hunde" in svg


def test_voyage_scene_fits_eight_players():
    result = RoundResult(captain=0, crew=[1, 2, 3, 4, 5, 6, 7], deserters=[], bid=1, answer=2)
    colours = ["#000001", "#000002", "#000003", "#000004"] * 2

    svg = voyage_scene(result, players(*colours))

    for x, width in re.findall(r'<rect x="(\d+)" y="\d+" width="(\d+)"', svg):
        assert int(x) + int(width) <= 120


def test_lone_captain_who_makes_it_sails_away_with_a_treasure_chest():
    result = RoundResult(captain=0, crew=[], deserters=[1, 2], bid=10, answer=20)

    svg = voyage_scene(result, players("#ff004d", "#29adff", "#00e436"))

    assert 'class="animate-twinkle"' in svg
    assert 'class="animate-cheer"' not in svg


def test_lone_captain_who_sinks_makes_the_deserters_cheer():
    result = RoundResult(captain=0, crew=[], deserters=[1, 2], bid=99, answer=20)

    svg = voyage_scene(result, players("#ff004d", "#29adff", "#00e436"))

    assert svg.count('class="animate-cheer"') == 2
    assert 'class="animate-twinkle"' not in svg


def test_a_normal_round_has_no_chest_and_no_cheering():
    result = RoundResult(captain=0, crew=[1], deserters=[2], bid=10, answer=20)

    svg = voyage_scene(result, players("#ff004d", "#29adff", "#00e436"))

    assert "animate-twinkle" not in svg and "animate-cheer" not in svg
