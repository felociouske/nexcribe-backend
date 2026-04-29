from rest_framework import serializers
from .models import Plan, UserPlan


class PlanSerializer(serializers.ModelSerializer):
    price_usd = serializers.ReadOnlyField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Plan
        fields = [
            'id', 'category', 'category_display', 'level', 'name',
            'price_kes', 'price_usd', 'description', 'features_list',
            'writing_tasks_per_month', 'writing_max_pay_per_task_kes',
            'writing_revisions_per_task', 'writing_priority_queue',
            'transcription_tasks_per_month', 'transcription_max_audio_minutes',
            'transcription_max_pay_per_task_kes', 'transcription_difficulty_access',
            'gaming_plays_per_day', 'gaming_max_win_per_day_kes',
            'gaming_wheel_spins_per_day', 'gaming_games_unlocked',
            'gaming_leaderboard_bonus', 'gaming_tournament_access',
        ]


class UserPlanSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    category = serializers.ReadOnlyField()

    class Meta:
        model = UserPlan
        fields = [
            'id', 'plan', 'category', 'status', 'purchased_at',
            'transaction_code', 'writing_tasks_used', 'transcription_tasks_used',
            'gaming_plays_today', 'wheel_spins_today',
        ]
