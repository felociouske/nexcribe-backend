from django.db import models
from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'writing_categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class WritingJob(TimeStampedModel):
    STATUS_OPEN = 'OPEN'
    STATUS_ASSIGNED = 'ASSIGNED'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    DIFFICULTY_BASIC = 'BASIC'
    DIFFICULTY_INTERMEDIATE = 'INTERMEDIATE'
    DIFFICULTY_ADVANCED = 'ADVANCED'
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BASIC, 'Basic'),
        (DIFFICULTY_INTERMEDIATE, 'Intermediate'),
        (DIFFICULTY_ADVANCED, 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    budget_kes = models.DecimalField(max_digits=10, decimal_places=2)
    word_count_required = models.PositiveIntegerField(default=500)
    difficulty = models.CharField(
        max_length=15, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_BASIC
    )
    minimum_plan_level = models.PositiveSmallIntegerField(default=1)
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default=STATUS_OPEN
    )
    assigned_to = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_writing_jobs'
    )
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, related_name='created_writing_jobs'
    )
    instructions = models.TextField(blank=True)

    # Submission — actual file uploaded by user
    submission_file = models.FileField(
        upload_to='writing_submissions/', null=True, blank=True
    )
    submission_filename = models.CharField(max_length=255, blank=True)
    submission_word_count = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    admin_feedback = models.TextField(blank=True)
    # Transaction code credited on approval
    payment_transaction_code = models.CharField(max_length=20, blank=True)
    payment_amount_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        db_table = 'writing_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} [{self.status}]'

    @property
    def budget_usd(self):
        from django.conf import settings
        return round(float(self.budget_kes) / settings.KES_TO_USD_RATE, 2)


class WritingJobHistory(TimeStampedModel):
    job = models.ForeignKey(
        WritingJob, on_delete=models.CASCADE, related_name='history'
    )
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    note = models.CharField(max_length=500, blank=True)
    transaction_code = models.CharField(max_length=20, blank=True)
    amount_usd = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        db_table = 'writing_job_history'
        ordering = ['-created_at']