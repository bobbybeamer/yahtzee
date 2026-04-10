from django.urls import path
from . import views

urlpatterns = [
    path('favicon.ico', views.favicon_ico, name='favicon_ico'),
    path('favicon.svg', views.favicon_svg, name='favicon_svg'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('social-preview.svg', views.social_preview_svg, name='social_preview'),
    path('', views.home, name='home'),
    path('yahtzee/', views.index, name='index'),
    path('yahtzee/play/', views.play_game, name='play_game'),
    path('yahtzee/start/', views.start_game, name='start_game'),
    path('yahtzee/roll/', views.roll_dice_view, name='roll_dice'),
    path('yahtzee/choose/', views.choose_category, name='choose_category'),
    path('yahtzee/game_over/', views.game_over, name='game_over'),
    path('yahtzee/rules/', views.rules, name='rules'),
    path('maths-square/', views.maths_square, name='maths_square'),
]
