from django.db import models
from apps.core.models import TimeStampedModel


GAME_TYPES = [
    ('quiz', 'Quiz'),
    ('trivia', 'Trivia'),
    ('word_puzzle', 'Word Puzzle'),
    ('slots', 'Slots Machine'),
    ('number_match', 'Number Match'),
    ('memory', 'Memory Game'),
    ('speed_type', 'Speed Typing'),
    ('vip_challenge', 'VIP Challenge'),
]


class Game(TimeStampedModel):
    slug = models.CharField(max_length=30, unique=True, choices=GAME_TYPES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    min_plan_level = models.PositiveSmallIntegerField(default=1)
    reward_per_win_kes = models.DecimalField(max_digits=8, decimal_places=2, default=50)
    reward_per_win_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=10, blank=True)   # emoji icon

    class Meta:
        db_table = 'games'
        ordering = ['min_plan_level']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.reward_per_win_usd:
            from django.conf import settings
            from decimal import Decimal
            self.reward_per_win_usd = (
                Decimal(str(self.reward_per_win_kes)) /
                Decimal(str(settings.KES_TO_USD_RATE))
            ).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)


class QuizQuestion(TimeStampedModel):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[
        ('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')
    ])
    difficulty = models.CharField(max_length=10, choices=[
        ('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')
    ], default='easy')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'quiz_questions'

    def __str__(self):
        return self.question[:80]


class GameSession(TimeStampedModel):
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_EXPIRED = 'EXPIRED'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_EXPIRED, 'Expired'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='game_sessions')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='sessions')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    reward_earned_kes = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    reward_earned_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    reward_credited = models.BooleanField(default=False)
    transaction_code = models.CharField(max_length=20, blank=True)
    # Server-generated token to validate result submission
    session_token = models.CharField(max_length=64, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    # Store question IDs served so we can verify answers server-side
    question_ids = models.JSONField(default=list)
    correct_answers = models.JSONField(default=dict)  # {question_id: correct_option}

    class Meta:
        db_table = 'game_sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.game.name} [{self.status}]'


class GameLeaderboard(TimeStampedModel):
    """Daily leaderboard snapshot — recreated each day."""
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='leaderboard_entries')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    date = models.DateField()
    total_score = models.PositiveIntegerField(default=0)
    sessions_played = models.PositiveIntegerField(default=0)
    total_earned_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    rank = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'game_leaderboard'
        unique_together = ['game', 'user', 'date']
        ordering = ['rank']
