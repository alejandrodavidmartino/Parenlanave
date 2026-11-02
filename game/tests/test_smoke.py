from django.urls import reverse


def test_title_screen_shows_the_scene_and_the_menu(client):
    response = client.get(reverse("game:title"))

    content = response.content.decode()
    assert response.status_code == 200
    assert "Atraquen" in content
    assert "Un pirata en un muelle de madera" in content  # the scene
    for name in ("new", "options", "rules"):
        assert f'href="{reverse(f"game:{name}")}"' in content


def test_rules_screen_shows_the_engine_scoring(client):
    response = client.get(reverse("game:rules"))

    content = response.content.decode()
    assert "Cómo se juega" in content
    assert "<td>⚓ Capitán</td><td>4</td><td>-1</td>" in content


def test_options_screen_has_animation_music_and_sound_switches(client):
    response = client.get(reverse("game:options"))

    content = response.content.decode()
    for option in ("animations", "music", "sfx"):
        assert f"onclick=\"toggleOption('{option}')\"" in content
    assert "Música" in content and "Efectos de sonido" in content


def test_title_screen_plays_the_shanty_and_every_page_loads_the_sounds(client):
    content = client.get(reverse("game:title")).content.decode()

    assert 'data-music="title"' in content
    assert "js/sound.js" in content


def test_rules_screen_explains_every_step_of_a_round(client):
    content = client.get(reverse("game:rules")).content.decode()

    for step in (
        "Empieza la ronda:",
        "Turnos de los jugadores:",
        "Si alguien se baja:",
        "Fin de las apuestas:",
        "¿El barco zarpa o naufraga?",
        "Nueva ronda:",
        "Objetivo:",
    ):
        assert step in content
