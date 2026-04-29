from django.db import models
from apps.core.models import TimeStampedModel


class WheelConfig(TimeStampedModel):
    name = models.CharField(max_length=100, default='Nexcribe Lucky Wheel')
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'wheel_configs'

    def __str__(self):
        return self.name


class WheelSlice(TimeStampedModel):
    REWARD_CASH = 'CASH'
    REWARD_SPINS = 'SPINS'
    REWARD_NONE = 'NONE'
    REWARD_TYPES = [
        (REWARD_CASH, 'Cash Credit'),
        (REWARD_SPINS, 'Bonus Spins'),
        (REWARD_NONE, 'No Reward (Try Again)'),
    ]

    wheel = models.ForeignKey(WheelConfig, on_delete=models.CASCADE, related_name='slices')
    label = models.CharField(max_length=50)
    reward_type = models.CharField(max_length=10, choices=REWARD_TYPES, default=REWARD_CASH)
    reward_value_kes = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    reward_spins = models.PositiveIntegerField(default=0)
    probability = models.DecimalField(max_digits=5, decimal_places=4)  # 0.0000 – 1.0000; all slices must sum to 1
    color_hex = models.CharField(max_length=7, default='#0a7c5c')
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'wheel_slices'
        ordering = ['display_order']

    def __str__(self):
        return f'{self.label} ({self.probability * 100:.1f}%)'

    @property
    def reward_value_usd(self):
        from django.conf import settings
        from decimal import Decimal
        return (Decimal(str(self.reward_value_kes)) /
                Decimal(str(settings.KES_TO_USD_RATE))).quantize(Decimal('0.01'))


class SpinResult(TimeStampedModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='spin_results')
    wheel = models.ForeignKey(WheelConfig, on_delete=models.CASCADE)
    slice_won = models.ForeignKey(WheelSlice, on_delete=models.SET_NULL, null=True)
    reward_type = models.CharField(max_length=10)
    reward_kes = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    reward_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bonus_spins = models.PositiveIntegerField(default=0)
    transaction_code = models.CharField(max_length=20, blank=True)
    credited = models.BooleanField(default=False)

    class Meta:
        db_table = 'spin_results'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.slice_won.label if self.slice_won else "N/A"}'
