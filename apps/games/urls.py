from django.urls import path
from .views import (
    GameListView, StartGameView, SubmitGameResultView,
    MyGameHistoryView, LeaderboardView, AdminGameStatsView,
)

urlpatterns = [
    path('', GameListView.as_view(), name='game-list'),
    path('history/', MyGameHistoryView.as_view(), name='game-history'),
    path('stats/', AdminGameStatsView.as_view(), name='game-stats'),
    path('<str:game_slug>/start/', StartGameView.as_view(), name='game-start'),
    path('<str:game_slug>/leaderboard/', LeaderboardView.as_view(), name='game-leaderboard'),
    path('sessions/<uuid:session_id>/submit/', SubmitGameResultView.as_view(), name='game-submit'),
]
