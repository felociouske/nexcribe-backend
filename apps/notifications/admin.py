from django.contrib import admin
from .models import Notification, EmailLog
from django import forms


class SendRemarkForm(forms.Form):
    user_email = forms.EmailField(label='User Email')
    title = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    link = forms.CharField(max_length=200, required=False)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'admin_remark', 'created_at']
    list_filter = ['type', 'is_read']
    search_fields = ['user__email', 'title', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Notification', {
            'fields': ('user', 'type', 'title', 'message', 'link', 'is_read', 'metadata')
        }),
        ('Admin Remark', {
            'fields': ('admin_remark', 'sent_by_admin'),
            'description': 'Add a personal remark visible to the user.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.sent_by_admin and obj.admin_remark:
            obj.sent_by_admin = request.user
        super().save_model(request, obj, form, change)

    actions = ['send_remark_to_selected']

    def send_remark_to_selected(self, request, queryset):
        """Mark selected notifications with admin remark."""
        remark = request.POST.get('remark_text', '')
        if remark:
            queryset.update(admin_remark=remark, sent_by_admin=request.user)
            self.message_user(request, f'Remark added to {queryset.count()} notification(s).')
    send_remark_to_selected.short_description = 'Add remark to selected notifications'


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_email', 'email_type', 'subject', 'status', 'created_at']
    list_filter = ['email_type', 'status']
    search_fields = ['recipient_email', 'subject']
    ordering = ['-created_at']
    readonly_fields = ['user', 'email_type', 'recipient_email', 'subject', 'status', 'error_message']