from django.urls import path

from . import views

app_name = "game"

urlpatterns = [
    path("", views.title, name="title"),
    path("new/", views.new_game, name="new"),
    path("rules/", views.rules, name="rules"),
    path("options/", views.options, name="options"),
    path("games/<int:pk>/", views.game_detail, name="detail"),
    path("games/<int:pk>/next-round/", views.next_round, name="next_round"),
    path("games/<int:pk>/open/", views.open_round, name="open_round"),
    path("games/<int:pk>/play/", views.play, name="play"),
    path("games/<int:pk>/reveal/", views.reveal, name="reveal"),
]
