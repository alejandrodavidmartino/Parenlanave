from django.urls import path

from . import views

app_name = "game"

urlpatterns = [
    path("", views.home, name="home"),
    path("games/<int:pk>/", views.game_detail, name="detail"),
    path("games/<int:pk>/next-round/", views.next_round, name="next_round"),
    path("games/<int:pk>/open/", views.open_round, name="open_round"),
    path("games/<int:pk>/play/", views.play, name="play"),
]
