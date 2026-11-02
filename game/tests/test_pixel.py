import re

from django.template import Context, Template

from game.templatetags.pixel import SPRITES, sprite, title_scene


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
