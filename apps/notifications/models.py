from django.db import models
from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    TYPE_CHOICES = [
        ('COMMISSION', 'Commission Earned'),
        ('REFERRAL', 'New Referral'),
        ('PLAN_PURCHASE', 'Plan Purchased'),
        ('WITHDRAWAL', 'Withdrawal Update'),
        ('DEPOSIT', 'Deposit Update'),
        ('TASK_APPROVED', 'Task Approved'),
        ('TASK_REJECTED', 'Task Rejected'),
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('GAME_REWARD', 'Game Reward'),
        ('SPIN_WIN', 'Wheel Spin Win'),
        ('SYSTEM', 'System Message'),
        ('ADMIN_REMARK', 'Admin Remark'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    # Admin can add a personal remark to any notification
    admin_remark = models.TextField(blank=True)
    sent_by_admin = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sent_notifications'
    )

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.type} — {"read" if self.is_read else "unread"}'


class EmailLog(TimeStampedModel):
    STATUS_SENT = 'SENT'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [(STATUS_SENT, 'Sent'), (STATUS_FAILED, 'Failed')]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='email_logs')
    email_type = models.CharField(max_length=50)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_SENT)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'email_logs'
        ordering = ['-created_at']