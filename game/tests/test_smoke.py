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


def test_options_screen_has_the_animations_switch(client):
    response = client.get(reverse("game:options"))

    content = response.content.decode()
    assert "Animaciones" in content
    assert 'onclick="toggleAnimations()"' in content
