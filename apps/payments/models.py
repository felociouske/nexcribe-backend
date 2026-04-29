from django.db import models
from apps.core.models import TimeStampedModel


class DepositRequest(TimeStampedModel):
    """Manual M-Pesa deposit submitted by user, approved by admin."""
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='deposit_requests')
    transaction_code = models.CharField(max_length=20, unique=True, blank=True)
    mpesa_code = models.CharField(max_length=30)          # M-Pesa confirmation code
    phone_number = models.CharField(max_length=20)
    amount_kes = models.DecimalField(max_digits=10, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_note = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='processed_deposits'
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'deposit_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.mpesa_code} | {self.user.email} | KES {self.amount_kes} [{self.status}]'

    def save(self, *args, **kwargs):
        if not self.transaction_code:
            from apps.core.models import generate_transaction_code
            code = generate_transaction_code()
            while DepositRequest.objects.filter(transaction_code=code).exists():
                code = generate_transaction_code()
            self.transaction_code = code
        super().save(*args, **kwargs)


class WithdrawalRequest(TimeStampedModel):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    METHOD_MPESA = 'MPESA'
    METHOD_CARD = 'CARD'
    METHOD_CHOICES = [
        (METHOD_MPESA, 'M-Pesa'),
        (METHOD_CARD, 'Card'),
    ]

    WALLET_ACCOUNT = 'ACCOUNT'
    WALLET_YIELDS = 'YIELDS'
    WALLET_CHOICES = [
        (WALLET_ACCOUNT, 'Account Wallet'),
        (WALLET_YIELDS, 'Yields Wallet'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='withdrawal_requests')
    transaction_code = models.CharField(max_length=20, unique=True, blank=True)
    wallet_type = models.CharField(max_length=10, choices=WALLET_CHOICES)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    amount_kes = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True)
    account_details = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_note = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='processed_withdrawals'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'withdrawal_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.transaction_code} | {self.user.email} | ${self.amount_usd} [{self.status}]'

    def save(self, *args, **kwargs):
        if not self.transaction_code:
            from apps.core.models import generate_transaction_code
            code = generate_transaction_code()
            while WithdrawalRequest.objects.filter(transaction_code=code).exists():
                code = generate_transaction_code()
            self.transaction_code = code
        super().save(*args, **kwargs)