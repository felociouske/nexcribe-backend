from django.db import models
from apps.core.models import TimeStampedModel
from django.conf import settings


CATEGORY_WRITING = 'WRITING'
CATEGORY_TRANSCRIPTION = 'TRANSCRIPTION'
CATEGORY_GAMING = 'GAMING'

CATEGORY_CHOICES = [
    (CATEGORY_WRITING, 'Writing'),
    (CATEGORY_TRANSCRIPTION, 'Transcription'),
    (CATEGORY_GAMING, 'Gaming'),
]


class Plan(TimeStampedModel):
    """
    A purchasable plan for a specific category and level.
    Plans are LIFETIME — they never expire or reset.
    Task limits are total tasks available on the plan.
    9999 = unlimited.
    """
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    level = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=50)
    price_kes = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    # ── Writing-specific limits (total tasks for lifetime of plan) ──
    writing_tasks_per_month = models.PositiveIntegerField(default=0)  # total tasks on this plan
    writing_max_pay_per_task_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    writing_revisions_per_task = models.PositiveIntegerField(default=0)
    writing_priority_queue = models.BooleanField(default=False)
    writing_direct_assignments = models.BooleanField(default=False)

    # ── Transcription-specific limits (total tasks for lifetime of plan) ──
    transcription_tasks_per_month = models.PositiveIntegerField(default=0)  # total tasks
    transcription_max_audio_minutes = models.PositiveIntegerField(default=9999)
    transcription_max_pay_per_task_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transcription_difficulty_access = models.CharField(
        max_length=20, default='BASIC',
        choices=[('BASIC', 'Basic'), ('EASY', 'Easy'), ('MEDIUM', 'Medium'),
                 ('HARD', 'Hard'), ('ALL', 'All')]
    )
    transcription_priority_queue = models.BooleanField(default=False)

    # ── Gaming-specific limits ──
    gaming_plays_per_day = models.PositiveIntegerField(default=0)   # 0 = unlimited
    gaming_max_win_per_day_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gaming_wheel_spins_per_day = models.PositiveIntegerField(default=0)
    gaming_games_unlocked = models.JSONField(default=list)
    gaming_leaderboard_bonus = models.BooleanField(default=False)
    gaming_tournament_access = models.BooleanField(default=False)

    # ── Description / marketing ──
    description = models.TextField(blank=True)
    features_list = models.JSONField(default=list)

    class Meta:
        db_table = 'plans'
        unique_together = ['category', 'level']
        ordering = ['category', 'level']

    def __str__(self):
        return f'{self.get_category_display()} — {self.name} (Level {self.level})'

    @property
    def price_usd(self):
        return round(float(self.price_kes) / settings.KES_TO_USD_RATE, 2)

    @property
    def writing_tasks_total(self):
        return self.writing_tasks_per_month

    @property
    def transcription_tasks_total(self):
        return self.transcription_tasks_per_month


class UserPlan(TimeStampedModel):
    """
    A user's active plan.
    Plans are LIFETIME — status only changes to EXPIRED when user
    purchases a higher plan in the same category (the old one is expired).
    Task counters count up and never reset.
    """
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_CHOICES = [(STATUS_ACTIVE, 'Active'), (STATUS_EXPIRED, 'Expired')]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='user_plans')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='user_plans')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    transaction_code = models.CharField(max_length=20, blank=True)

    # Lifetime usage counters — count up, never reset
    writing_tasks_used = models.PositiveIntegerField(default=0)
    transcription_tasks_used = models.PositiveIntegerField(default=0)

    # Gaming resets daily (plays/spins are per-day limits, not lifetime)
    gaming_plays_today = models.PositiveIntegerField(default=0)
    wheel_spins_today = models.PositiveIntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'user_plans'
        unique_together = ['user', 'plan']

    def __str__(self):
        return f'{self.user.email} — {self.plan}'

    @property
    def category(self):
        return self.plan.category

    @property
    def writing_tasks_remaining(self):
        limit = self.plan.writing_tasks_per_month
        if limit == 9999:
            return 9999
        return max(0, limit - self.writing_tasks_used)

    @property
    def transcription_tasks_remaining(self):
        limit = self.plan.transcription_tasks_per_month
        if limit == 9999:
            return 9999
        return max(0, limit - self.transcription_tasks_used)

    def reset_daily_counters(self):
        """Only gaming plays and wheel spins reset daily."""
        from django.utils import timezone
        today = timezone.now().date()
        if self.last_reset_date < today:
            self.gaming_plays_today = 0
            self.wheel_spins_today = 0
            self.last_reset_date = today
            self.save(update_fields=['gaming_plays_today', 'wheel_spins_today', 'last_reset_date'])