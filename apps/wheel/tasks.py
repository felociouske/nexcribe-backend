from celery import shared_task


@shared_task
def reset_daily_spins():
    """Reset daily wheel spin counters. Runs at midnight via Celery Beat."""
    from apps.plans.models import UserPlan
    from django.utils import timezone
    today = timezone.now().date()
    stale = UserPlan.objects.filter(
        plan__category='GAMING',
        status='ACTIVE',
        last_reset_date__lt=today,
    )
    count = stale.count()
    stale.update(wheel_spins_today=0, last_reset_date=today)
    return {'reset_count': count}


@shared_task
def seed_wheel():
    """Seed the default lucky wheel configuration."""
    from apps.wheel.models import WheelConfig, WheelSlice
    from decimal import Decimal

    wheel, created = WheelConfig.objects.get_or_create(
        name='Nexcribe Lucky Wheel',
        defaults={'is_active': True, 'description': 'Spin daily for cash and bonus spins!'}
    )

    if not created and wheel.slices.exists():
        return {'status': 'already seeded'}

    slices = [
        {'label': 'KES 50',       'reward_type': 'CASH',  'reward_value_kes': 50,   'probability': Decimal('0.2500'), 'color_hex': '#0a7c5c', 'display_order': 1},
        {'label': 'KES 100',      'reward_type': 'CASH',  'reward_value_kes': 100,  'probability': Decimal('0.1500'), 'color_hex': '#11b886', 'display_order': 2},
        {'label': 'Try Again',    'reward_type': 'NONE',  'reward_value_kes': 0,    'probability': Decimal('0.2000'), 'color_hex': '#6b7280', 'display_order': 3},
        {'label': 'KES 200',      'reward_type': 'CASH',  'reward_value_kes': 200,  'probability': Decimal('0.1000'), 'color_hex': '#e05a2b', 'display_order': 4},
        {'label': '2 Bonus Spins','reward_type': 'SPINS', 'reward_spins': 2,        'probability': Decimal('0.1200'), 'color_hex': '#1d4ed8', 'display_order': 5},
        {'label': 'KES 500',      'reward_type': 'CASH',  'reward_value_kes': 500,  'probability': Decimal('0.0500'), 'color_hex': '#7c3aed', 'display_order': 6},
        {'label': 'Try Again',    'reward_type': 'NONE',  'reward_value_kes': 0,    'probability': Decimal('0.1000'), 'color_hex': '#9ca3af', 'display_order': 7},
        {'label': 'KES 1,000',    'reward_type': 'CASH',  'reward_value_kes': 1000, 'probability': Decimal('0.0200'), 'color_hex': '#dc2626', 'display_order': 8},
        {'label': 'KES 25',       'reward_type': 'CASH',  'reward_value_kes': 25,   'probability': Decimal('0.0800'), 'color_hex': '#059669', 'display_order': 9},
        {'label': '5 Bonus Spins','reward_type': 'SPINS', 'reward_spins': 5,        'probability': Decimal('0.0300'), 'color_hex': '#0891b2', 'display_order': 10},
    ]

    for s in slices:
        WheelSlice.objects.create(wheel=wheel, **s)

    return {'status': 'seeded', 'slices': len(slices)}
