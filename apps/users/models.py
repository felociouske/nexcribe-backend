import uuid
import random
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel, generate_referral_code


def generate_virtual_card_number():
    """Generate a 16-digit virtual card number in groups of 4."""
    groups = [str(random.randint(1000, 9999)) for _ in range(4)]
    groups[0] = str(random.randint(4000, 4999))  
    return ' '.join(groups)


def generate_card_expiry():
    from datetime import date
    today = date.today()
    exp_year = today.year + 3
    return f"{today.month:02d}/{str(exp_year)[-2:]}"


def generate_cvv():
    return str(random.randint(100, 999))


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username


class Profile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    country = models.CharField(max_length=100, blank=True, default='Kenya')
    referral_code = models.CharField(max_length=20, unique=True, default=generate_referral_code)
    referred_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='referrals'
    )
    total_referrals = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'profiles'

    def __str__(self):
        return f'Profile({self.user.email})'


class VirtualCard(TimeStampedModel):
    """Auto-generated virtual card for each user account."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='virtual_card')
    card_number = models.CharField(max_length=19, default=generate_virtual_card_number)
    expiry = models.CharField(max_length=5, default=generate_card_expiry)
    cvv = models.CharField(max_length=3, default=generate_cvv)
    card_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'virtual_cards'

    def __str__(self):
        return f'Card({self.user.email}) {self.card_number}'

    def save(self, *args, **kwargs):
        if not self.card_name:
            self.card_name = self.user.full_name.upper() or self.user.username.upper()
        super().save(*args, **kwargs)


class AccountWallet(TimeStampedModel):
    """Earnings from writing, transcription, games, wheel."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account_wallet')
    balance_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pending_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_earned_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_withdrawn_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'account_wallets'

    def __str__(self):
        return f'AccountWallet({self.user.email}) ${self.balance_usd}'

    @property
    def balance_kes(self):
        from django.conf import settings
        return float(self.balance_usd) * settings.KES_TO_USD_RATE


class YieldsWallet(TimeStampedModel):
    """Referral commissions only."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='yields_wallet')
    balance_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pending_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_earned_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_withdrawn_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'yields_wallets'

    def __str__(self):
        return f'YieldsWallet({self.user.email}) ${self.balance_usd}'

    @property
    def balance_kes(self):
        from django.conf import settings
        return float(self.balance_usd) * settings.KES_TO_USD_RATE


class DepositWallet(TimeStampedModel):
    """Manual M-Pesa deposits — used to purchase plans."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='deposit_wallet')
    balance_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_deposited_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_spent_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'deposit_wallets'

    def __str__(self):
        return f'DepositWallet({self.user.email}) ${self.balance_usd}'

    @property
    def balance_kes(self):
        from django.conf import settings
        return float(self.balance_usd) * settings.KES_TO_USD_RATE


class CashbackWallet(TimeStampedModel):
    """Cashback rewards from platform activities."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cashback_wallet')
    balance_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_earned_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'cashback_wallets'

    def __str__(self):
        return f'CashbackWallet({self.user.email}) ${self.balance_usd}'

    @property
    def balance_kes(self):
        from django.conf import settings
        return float(self.balance_usd) * settings.KES_TO_USD_RATE


class Transaction(TimeStampedModel):
    CREDIT = 'CREDIT'
    DEBIT = 'DEBIT'
    TYPE_CHOICES = [(CREDIT, 'Credit'), (DEBIT, 'Debit')]

    ACCOUNT = 'ACCOUNT'
    YIELDS = 'YIELDS'
    DEPOSIT = 'DEPOSIT'
    CASHBACK = 'CASHBACK'
    WALLET_CHOICES = [
        (ACCOUNT, 'Account Wallet'),
        (YIELDS, 'Yields Wallet'),
        (DEPOSIT, 'Deposit Wallet'),
        (CASHBACK, 'Cashback Wallet'),
    ]

    SOURCE_CHOICES = [
        ('WRITING', 'Writing Task'),
        ('TRANSCRIPTION', 'Transcription Task'),
        ('GAME', 'Game Reward'),
        ('WHEEL', 'Wheel Spin'),
        ('REFERRAL', 'Referral Commission'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('DEPOSIT', 'Deposit'),
        ('PLAN_PURCHASE', 'Plan Purchase'),
        ('CASHBACK', 'Cashback'),
        ('REFUND', 'Refund'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REVERSED', 'Reversed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_code = models.CharField(max_length=20, unique=True)
    wallet_type = models.CharField(max_length=10, choices=WALLET_CHOICES)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    amount_kes = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='COMPLETED')
    reference = models.CharField(max_length=100, blank=True)
    balance_after_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.transaction_code} | {self.user.email} | ${self.amount_usd}'

    def save(self, *args, **kwargs):
        if not self.transaction_code:
            from apps.core.models import generate_transaction_code
            code = generate_transaction_code()
            while Transaction.objects.filter(transaction_code=code).exists():
                code = generate_transaction_code()
            self.transaction_code = code
        super().save(*args, **kwargs)


class EmailVerificationToken(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'email_verification_tokens'

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()


class PasswordResetToken(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'password_reset_tokens'

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()