from django.contrib import admin
from .models import Game, QuizQuestion, GameSession, GameLeaderboard


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'min_plan_level', 'reward_per_win_kes', 'is_active']
    list_filter = ['is_active', 'min_plan_level']
    search_fields = ['name', 'slug']


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'game', 'correct_option', 'difficulty', 'is_active']
    list_filter = ['game', 'difficulty', 'is_active']
    search_fields = ['question']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'game', 'status', 'score', 'reward_earned_usd', 'reward_credited', 'created_at']
    list_filter = ['game', 'status', 'reward_credited']
    search_fields = ['user__email', 'transaction_code']
    readonly_fields = ['session_token', 'question_ids', 'correct_answers', 'transaction_code']
    ordering = ['-created_at']


@admin.register(GameLeaderboard)
class GameLeaderboardAdmin(admin.ModelAdmin):
    list_display = ['game', 'user', 'date', 'total_score', 'sessions_played', 'total_earned_usd']
    list_filter = ['game', 'date']
    ordering = ['-date', '-total_score']
