from django.contrib import admin
from .models import Plan, UserPlan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'level', 'price_kes', 'price_usd', 'is_active'
    ]
    list_filter = ['category', 'level', 'is_active']
    search_fields = ['name']
    ordering = ['category', 'level']
    readonly_fields = ['price_usd']

    fieldsets = (
        ('Basic Info', {
            'fields': ('category', 'level', 'name', 'price_kes', 'is_active', 'description', 'features_list')
        }),
        ('Writing Limits', {
            'classes': ('collapse',),
            'fields': (
                'writing_tasks_per_month', 'writing_max_pay_per_task_kes',
                'writing_revisions_per_task', 'writing_priority_queue',
                'writing_direct_assignments',
            )
        }),
        ('Transcription Limits', {
            'classes': ('collapse',),
            'fields': (
                'transcription_tasks_per_month', 'transcription_max_audio_minutes',
                'transcription_max_pay_per_task_kes', 'transcription_difficulty_access',
                'transcription_priority_queue',
            )
        }),
        ('Gaming Limits', {
            'classes': ('collapse',),
            'fields': (
                'gaming_plays_per_day', 'gaming_max_win_per_day_kes',
                'gaming_wheel_spins_per_day', 'gaming_games_unlocked',
                'gaming_leaderboard_bonus', 'gaming_tournament_access',
            )
        }),
    )


@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'plan', 'status', 'writing_tasks_used',
        'transcription_tasks_used', 'gaming_plays_today', 'purchased_at'
    ]
    list_filter = ['status', 'plan__category', 'plan__level']
    search_fields = ['user__email', 'transaction_code']
    ordering = ['-purchased_at']
    readonly_fields = ['transaction_code', 'purchased_at', 'last_reset_date']
