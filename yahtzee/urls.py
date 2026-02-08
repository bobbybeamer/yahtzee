from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start_game, name='start_game'),
    path('roll/', views.roll_dice_view, name='roll_dice'),
    path('choose/', views.choose_category, name='choose_category'),
    path('game_over/', views.game_over, name='game_over'),
    path('rules/', views.rules, name='rules'),
]