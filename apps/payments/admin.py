from django.contrib import admin
from django.utils import timezone
from decimal import Decimal
from django.conf import settings
from django.db import transaction as db_transaction

from .models import WithdrawalRequest, DepositRequest


@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'mpesa_code', 'amount_kes', 'phone_number', 'status', 'created_at', 'processed_at']
    list_filter = ['status']
    search_fields = ['mpesa_code', 'user__email', 'phone_number']
    ordering = ['-created_at']
    readonly_fields = ['user', 'mpesa_code', 'amount_kes', 'phone_number', 'created_at']
    actions = ['approve_deposits', 'reject_deposits']

    def save_model(self, request, obj, form, change):
        """
        Intercept status changes made by opening the record and saving.
        If status changed to APPROVED or REJECTED, run full processing logic
        instead of a plain save().
        """
        if not change:
            super().save_model(request, obj, form, change)
            return

        original = DepositRequest.objects.get(pk=obj.pk)

        # Only act if status actually changed from PENDING
        if original.status == DepositRequest.STATUS_PENDING and obj.status != DepositRequest.STATUS_PENDING:
            if obj.status == DepositRequest.STATUS_APPROVED:
                self._process_deposit_approval(request, obj)
            elif obj.status == DepositRequest.STATUS_REJECTED:
                self._process_deposit_rejection(request, obj)
        else:
            super().save_model(request, obj, form, change)

    def _process_deposit_approval(self, request, d):
        from apps.users.models import Transaction, DepositWallet
        from apps.notifications.utils import create_notification

        with db_transaction.atomic():
            amount_kes = Decimal(str(d.amount_kes))
            amount_usd = (
                amount_kes / Decimal(str(settings.KES_TO_USD_RATE))
            ).quantize(Decimal('0.01'))

            wallet, _ = DepositWallet.objects.select_for_update().get_or_create(user=d.user)
            wallet.balance_usd         += amount_usd
            wallet.total_deposited_usd += amount_usd
            wallet.save(update_fields=['balance_usd', 'total_deposited_usd', 'updated_at'])

            Transaction.objects.create(
                user=d.user,
                wallet_type='DEPOSIT',
                type='CREDIT',
                amount_usd=amount_usd,
                amount_kes=amount_kes,
                source='DEPOSIT',
                description=f'M-Pesa deposit approved — {d.mpesa_code}',
                status='COMPLETED',
                reference=d.mpesa_code,
                balance_after_usd=wallet.balance_usd,
            )

            d.processed_by = request.user
            d.processed_at = timezone.now()
            d.save()

            try:
                create_notification(
                    d.user, 'DEPOSIT',
                    'Deposit Approved',
                    f'Your deposit of KES {amount_kes:,.0f} (${amount_usd}) has been credited to your Deposit Wallet.',
                    '/dashboard/wallet',
                )
            except Exception:
                pass

            # Send email — runs synchronously, no Celery needed
            try:
                from apps.notifications.utils import send_html_email
                send_html_email(
                    user=d.user,
                    email_type='DEPOSIT_APPROVED',
                    subject='Your deposit has been approved — Nexcribe',
                    template_name='deposit_update.html',
                    context={
                        'status': 'APPROVED',
                        'amount_usd': str(amount_usd),
                        'amount_kes': str(amount_kes),
                        'mpesa_code': d.mpesa_code,
                    },
                )
            except Exception:
                pass

    def _process_deposit_rejection(self, request, d):
        from apps.notifications.utils import create_notification

        with db_transaction.atomic():
            d.processed_by = request.user
            d.processed_at = timezone.now()
            d.save()

            try:
                create_notification(
                    d.user, 'DEPOSIT',
                    'Deposit Rejected',
                    f'Your deposit of KES {d.amount_kes} (M-Pesa: {d.mpesa_code}) was rejected. '
                    f'Please contact support if you believe this is an error.',
                    '/dashboard/wallet',
                )
            except Exception:
                pass

            try:
                from apps.notifications.utils import send_html_email
                send_html_email(
                    user=d.user,
                    email_type='DEPOSIT_REJECTED',
                    subject='Your deposit could not be processed — Nexcribe',
                    template_name='deposit_update.html',
                    context={
                        'status': 'REJECTED',
                        'amount_usd': None,
                        'amount_kes': str(d.amount_kes),
                        'mpesa_code': d.mpesa_code,
                    },
                )
            except Exception:
                pass

    def approve_deposits(self, request, queryset):
        pending = queryset.filter(status=DepositRequest.STATUS_PENDING)
        count = 0
        for d in pending:
            self._process_deposit_approval(request, d)
            count += 1
        self.message_user(request, f'{count} deposit(s) approved and wallets credited.')
    approve_deposits.short_description = 'Approve selected deposits'

    def reject_deposits(self, request, queryset):
        pending = queryset.filter(status=DepositRequest.STATUS_PENDING)
        count = 0
        for d in pending:
            self._process_deposit_rejection(request, d)
            count += 1
        self.message_user(request, f'{count} deposit(s) rejected.')
    reject_deposits.short_description = 'Reject selected deposits'


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_code', 'user', 'wallet_type', 'amount_usd',
        'method', 'status', 'created_at', 'processed_at',
    ]
    list_filter   = ['status', 'wallet_type', 'method']
    search_fields = ['transaction_code', 'user__email', 'phone_number']
    ordering      = ['-created_at']
    readonly_fields = [
        'user', 'transaction_code', 'wallet_type', 'amount_usd',
        'amount_kes', 'method', 'phone_number', 'created_at',
    ]
    actions = ['approve_withdrawals', 'reject_withdrawals']

    def save_model(self, request, obj, form, change):
        """
        Intercept status changes made by opening the record and saving.
        If status changed to APPROVED or REJECTED, run full processing logic
        instead of a plain save().
        """
        if not change:
            super().save_model(request, obj, form, change)
            return

        original = WithdrawalRequest.objects.get(pk=obj.pk)

        # Only act if status actually changed from PENDING
        if original.status == WithdrawalRequest.STATUS_PENDING and obj.status != WithdrawalRequest.STATUS_PENDING:
            if obj.status == WithdrawalRequest.STATUS_APPROVED:
                self._process_approval(request, obj)
            elif obj.status == WithdrawalRequest.STATUS_REJECTED:
                self._process_rejection(request, obj)
        else:
            super().save_model(request, obj, form, change)

    def _get_wallet(self, w):
        from apps.users.models import AccountWallet, YieldsWallet
        if w.wallet_type == 'ACCOUNT':
            return AccountWallet.objects.select_for_update().get(user=w.user)
        return YieldsWallet.objects.select_for_update().get(user=w.user)

    def _process_approval(self, request, w):
        from apps.users.models import Transaction
        from apps.notifications.utils import create_notification

        with db_transaction.atomic():
            wallet = self._get_wallet(w)

            if wallet.pending_usd < w.amount_usd:
                self.message_user(
                    request,
                    f'Cannot approve {w.transaction_code}: pending ${wallet.pending_usd} < amount ${w.amount_usd}.',
                    level='WARNING',
                )
                return

            wallet.pending_usd         -= w.amount_usd
            wallet.total_withdrawn_usd += w.amount_usd
            wallet.save()

            w.status       = WithdrawalRequest.STATUS_APPROVED
            w.processed_by = request.user
            w.processed_at = timezone.now()
            w.save()

            Transaction.objects.filter(transaction_code=w.transaction_code).update(status='COMPLETED')

            try:
                wallet_label = 'Account Wallet' if w.wallet_type == 'ACCOUNT' else 'Yields Wallet'
                create_notification(
                    w.user, 'WITHDRAWAL',
                    'Withdrawal Approved',
                    f'Your withdrawal of ${w.amount_usd} (KES {w.amount_kes:,.0f}) from your '
                    f'{wallet_label} has been approved and sent to {w.phone_number}.',
                    '/dashboard/wallet',
                )
            except Exception:
                pass

    def _process_rejection(self, request, w):
        from apps.users.models import Transaction
        from apps.notifications.utils import create_notification

        with db_transaction.atomic():
            wallet = self._get_wallet(w)

            if wallet.pending_usd < w.amount_usd:
                self.message_user(
                    request,
                    f'Cannot reject {w.transaction_code}: pending ${wallet.pending_usd} < amount ${w.amount_usd}.',
                    level='WARNING',
                )
                return

            wallet.pending_usd -= w.amount_usd
            wallet.balance_usd += w.amount_usd
            wallet.save()

            w.status       = WithdrawalRequest.STATUS_REJECTED
            w.processed_by = request.user
            w.processed_at = timezone.now()
            w.save()

            Transaction.objects.filter(transaction_code=w.transaction_code).update(status='REVERSED')

            Transaction.objects.create(
                user=w.user,
                wallet_type=w.wallet_type,
                type='CREDIT',
                amount_usd=w.amount_usd,
                amount_kes=w.amount_kes,
                source='WITHDRAWAL_REVERSAL',
                description='Withdrawal rejected — funds returned to wallet.',
                status='COMPLETED',
                balance_after_usd=wallet.balance_usd,
            )

            try:
                wallet_label = 'Account Wallet' if w.wallet_type == 'ACCOUNT' else 'Yields Wallet'
                create_notification(
                    w.user, 'WITHDRAWAL',
                    'Withdrawal Rejected',
                    f'Your withdrawal of ${w.amount_usd} (KES {w.amount_kes:,.0f}) from your '
                    f'{wallet_label} has been rejected. The funds have been returned to your balance.',
                    '/dashboard/wallet',
                )
            except Exception:
                pass

    def approve_withdrawals(self, request, queryset):
        pending = queryset.filter(status=WithdrawalRequest.STATUS_PENDING)
        count = 0
        for w in pending:
            self._process_approval(request, w)
            count += 1
        self.message_user(request, f'{count} withdrawal(s) approved.')
    approve_withdrawals.short_description = 'Approve selected withdrawals'

    def reject_withdrawals(self, request, queryset):
        pending = queryset.filter(status=WithdrawalRequest.STATUS_PENDING)
        count = 0
        for w in pending:
            self._process_rejection(request, w)
            count += 1
        self.message_user(request, f'{count} withdrawal(s) rejected and balances restored.')
    reject_withdrawals.short_description = 'Reject selected withdrawals'