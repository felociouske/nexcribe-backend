from django.db import models
from apps.core.models import TimeStampedModel

# ── Commission rates — 4 levels only ──
# L1 = direct referrer (60%), L2 = 15%, L3 = 5%, L4 = 3%
# Total paid out: 83% — platform keeps 17%
COMMISSION_RATES = {
    1: 0.60,   # 60% — direct referrer
    2: 0.15,   # 15%
    3: 0.05,   #  5%
    4: 0.03,   #  3%
}

MAX_COMMISSION_LEVELS = 4


class AffiliateNode(TimeStampedModel):
    """Represents a user's position in the referral tree."""
    user = models.OneToOneField(
        'users.User', on_delete=models.CASCADE, related_name='affiliate_node'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children'
    )
    depth = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'affiliate_nodes'

    def __str__(self):
        return f'Node({self.user.email}) depth={self.depth}'

    def get_ancestors(self, max_levels=MAX_COMMISSION_LEVELS):
        """Return ancestor nodes up to max_levels, closest first."""
        ancestors = []
        current = self.parent
        while current and len(ancestors) < max_levels:
            ancestors.append(current)
            current = current.parent
        return ancestors


class Commission(TimeStampedModel):
    """A single commission credit earned by an upline user."""
    STATUS_PENDING = 'PENDING'
    STATUS_PAID = 'PAID'
    STATUS_FAILED = 'FAILED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_FAILED, 'Failed'),
    ]

    recipient = models.ForeignKey(
        'users.User', on_delete=models.CASCADE,
        related_name='commissions_received'
    )
    from_user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE,
        related_name='commissions_generated'
    )
    plan = models.ForeignKey(
        'plans.Plan', on_delete=models.SET_NULL, null=True,
        related_name='commissions'
    )
    level_depth = models.PositiveSmallIntegerField()     # 1-4
    rate = models.DecimalField(max_digits=5, decimal_places=4)
    plan_price_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_kes = models.DecimalField(max_digits=10, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=4)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PAID)
    transaction_code = models.CharField(max_length=20, blank=True)
    plan_purchase_txn = models.CharField(max_length=20, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'commissions'
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'L{self.level_depth} commission: {self.recipient.email} '
            f'← {self.from_user.email} | KES {self.amount_kes}'
        )