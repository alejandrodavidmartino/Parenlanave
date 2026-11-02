from django.urls import path

from . import views

app_name = "game"

urlpatterns = [
    path("", views.home, name="home"),
    path("games/<int:pk>/", views.game_detail, name="detail"),
]
