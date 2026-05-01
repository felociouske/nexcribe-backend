import uuid
import string
import random
from django.db import models


def generate_transaction_code():
    """Generate unique NX-TXN-XXXXXX code."""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=8))
    return f'NX-TXN-{suffix}'

def generate_referral_code():
    """Generate unique referral code like NX-REF-XXXXXX."""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f'NX-{suffix}'


class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
