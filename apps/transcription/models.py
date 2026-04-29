from django.db import models
from apps.core.models import TimeStampedModel


class TranscriptionTask(TimeStampedModel):
    STATUS_AVAILABLE = 'AVAILABLE'
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_RETIRED = 'RETIRED'
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_RETIRED, 'Retired'),
    ]

    DIFFICULTY_BASIC = 'BASIC'
    DIFFICULTY_EASY = 'EASY'
    DIFFICULTY_MEDIUM = 'MEDIUM'
    DIFFICULTY_HARD = 'HARD'
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BASIC, 'Basic'),
        (DIFFICULTY_EASY, 'Easy'),
        (DIFFICULTY_MEDIUM, 'Medium'),
        (DIFFICULTY_HARD, 'Hard'),
    ]

    SOURCE_ADMIN = 'ADMIN'
    SOURCE_LIBRIVOX = 'LIBRIVOX'
    SOURCE_CHOICES = [
        (SOURCE_ADMIN, 'Admin Upload'),
        (SOURCE_LIBRIVOX, 'LibriVox API'),
    ]

    MIN_PLAN_CHOICES = [(i, f'Level {i}') for i in range(1, 9)]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_LIBRIVOX)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_BASIC)
    language = models.CharField(max_length=50, default='English')
    duration_seconds = models.PositiveIntegerField(default=0)
    pay_kes = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_plan_level = models.PositiveSmallIntegerField(default=1, choices=MIN_PLAN_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)

    # LibriVox-sourced fields (no actual file stored in DB)
    librivox_id = models.CharField(max_length=50, blank=True)
    librivox_section_id = models.CharField(max_length=50, blank=True)
    audio_url = models.URLField(max_length=500, blank=True)    # external URL — not stored locally
    book_title = models.CharField(max_length=200, blank=True)
    book_author = models.CharField(max_length=200, blank=True)

    # Admin-upload fields — only filename stored, actual file on filesystem
    audio_filename = models.CharField(max_length=255, blank=True)
    # Admin-uploaded audio stored directly in the backend (served via /media/)
    audio_file = models.FileField(upload_to='transcription_audio/', null=True, blank=True)

    assigned_to = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_transcription_tasks'
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    claim_expires_at = models.DateTimeField(null=True, blank=True)  # 24hr lock

    class Meta:
        db_table = 'transcription_tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} [{self.status}]'

    @property
    def pay_usd(self):
        from django.conf import settings
        return round(float(self.pay_kes) / settings.KES_TO_USD_RATE, 2)

    @property
    def duration_minutes(self):
        return round(self.duration_seconds / 60, 1)

    def is_claim_expired(self):
        if not self.claim_expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.claim_expires_at


class TranscriptionSubmission(TimeStampedModel):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    task = models.ForeignKey(TranscriptionTask, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='transcription_submissions')
    # Only the transcript text is stored — no audio file in DB
    transcript_text = models.TextField()
    word_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_feedback = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_submissions'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    transaction_code = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'transcription_submissions'
        ordering = ['-created_at']
        unique_together = ['task', 'user']

    def __str__(self):
        return f'{self.user.email} → {self.task.title} [{self.status}]'