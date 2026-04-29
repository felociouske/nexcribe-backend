from django.contrib import admin
from .models import TranscriptionTask, TranscriptionSubmission


@admin.register(TranscriptionTask)
class TranscriptionTaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'source', 'difficulty', 'duration_minutes',
        'pay_kes', 'minimum_plan_level', 'status', 'assigned_to', 'created_at'
    ]
    list_filter = ['source', 'difficulty', 'status', 'language']
    search_fields = ['title', 'book_title', 'book_author', 'librivox_id']
    ordering = ['-created_at']
    readonly_fields = ['librivox_id', 'librivox_section_id', 'audio_url', 'assigned_at', 'claim_expires_at']

    def duration_minutes(self, obj):
        return f'{obj.duration_minutes} min'
    duration_minutes.short_description = 'Duration'


@admin.register(TranscriptionSubmission)
class TranscriptionSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'task', 'word_count', 'status', 'transaction_code', 'reviewed_at', 'created_at'
    ]
    list_filter = ['status']
    search_fields = ['user__email', 'task__title', 'transaction_code']
    ordering = ['-created_at']
    readonly_fields = ['user', 'task', 'transcript_text', 'word_count', 'transaction_code', 'created_at']
