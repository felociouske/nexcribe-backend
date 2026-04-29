from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from .models import User, Profile, AccountWallet, YieldsWallet, Transaction


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'full_name', 'is_verified', 'is_staff', 'date_joined']
    list_filter = ['is_verified', 'is_staff', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'username', 'password1', 'password2')}),
    )
    actions = ['send_activation_reminder']

    def send_activation_reminder(self, request, queryset):
        """
        Manually send an activation reminder email to selected users.
        Useful for targeting specific inactive accounts.
        """
        from apps.notifications.utils import send_html_email, create_notification
        from apps.writing.models import WritingJob
        from apps.transcription.models import TranscriptionTask
        from django.conf import settings

        sample_writing = list(
            WritingJob.objects.filter(status='OPEN', minimum_plan_level=1)
            .values('title', 'budget_kes')[:3]
        )
        sample_transcription = list(
            TranscriptionTask.objects.filter(status='AVAILABLE', minimum_plan_level=1)
            .values('title', 'pay_kes')[:3]
        )

        sent = 0
        failed = 0
        for user in queryset:
            try:
                send_html_email(
                    user=user,
                    email_type='INACTIVE_REMINDER',
                    subject='Tasks are waiting for you on Nexcribe',
                    template_name='inactive_reminder.html',
                    context={
                        'username': user.first_name or user.username,
                        'sample_writing': sample_writing,
                        'sample_transcription': sample_transcription,
                        'plans_url': f"{settings.FRONTEND_URL}/dashboard/plans",
                        'writing_count': WritingJob.objects.filter(status='OPEN').count(),
                        'transcription_count': TranscriptionTask.objects.filter(status='AVAILABLE').count(),
                    },
                )
                create_notification(
                    user, 'SYSTEM',
                    'Tasks are waiting for you!',
                    'There are writing and transcription tasks available. Activate a plan to start earning.',
                    '/dashboard/plans',
                )
                sent += 1
            except Exception as e:
                failed += 1
                self.message_user(request, f'Failed for {user.email}: {e}', level=messages.WARNING)

        self.message_user(request, f'Sent {sent} reminder email(s). {failed} failed.')
    send_activation_reminder.short_description = 'Send activation reminder email'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'referral_code', 'total_referrals', 'country']
    search_fields = ['user__email', 'referral_code']
    readonly_fields = ['referral_code']


@admin.register(AccountWallet)
class AccountWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance_usd', 'total_earned_usd', 'total_withdrawn_usd']
    search_fields = ['user__email']
    readonly_fields = ['balance_usd', 'pending_usd', 'total_earned_usd', 'total_withdrawn_usd']


@admin.register(YieldsWallet)
class YieldsWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance_usd', 'total_earned_usd', 'total_withdrawn_usd']
    search_fields = ['user__email']
    readonly_fields = ['balance_usd', 'pending_usd', 'total_earned_usd', 'total_withdrawn_usd']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_code', 'user', 'wallet_type', 'type', 'amount_usd', 'source', 'status', 'created_at']
    list_filter = ['wallet_type', 'type', 'source', 'status']
    search_fields = ['transaction_code', 'user__email', 'reference']
    ordering = ['-created_at']
    readonly_fields = ['transaction_code']