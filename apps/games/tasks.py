from celery import shared_task


@shared_task
def reset_daily_limits():
    """Reset daily game play counters for all users. Runs at midnight."""
    from apps.plans.models import UserPlan
    from django.utils import timezone
    today = timezone.now().date()
    stale = UserPlan.objects.filter(
        plan__category='GAMING',
        status='ACTIVE',
        last_reset_date__lt=today,
    )
    count = stale.count()
    stale.update(gaming_plays_today=0, wheel_spins_today=0, last_reset_date=today)
    return {'reset_count': count}


@shared_task
def seed_games():
    """Seed the initial game records if they don't exist."""
    from apps.games.models import Game
    from django.conf import settings
    from decimal import Decimal

    GAMES = [
        {'slug': 'quiz',         'name': 'Daily Quiz',       'min_plan_level': 1, 'reward_per_win_kes': 50,  'icon': '🧠'},
        {'slug': 'trivia',       'name': 'Trivia Challenge',  'min_plan_level': 2, 'reward_per_win_kes': 80,  'icon': '❓'},
        {'slug': 'word_puzzle',  'name': 'Word Puzzle',       'min_plan_level': 3, 'reward_per_win_kes': 100, 'icon': '🔤'},
        {'slug': 'slots',        'name': 'Slots Machine',     'min_plan_level': 4, 'reward_per_win_kes': 150, 'icon': '🎰'},
        {'slug': 'number_match', 'name': 'Number Match',      'min_plan_level': 5, 'reward_per_win_kes': 120, 'icon': '🔢'},
        {'slug': 'memory',       'name': 'Memory Game',       'min_plan_level': 6, 'reward_per_win_kes': 200, 'icon': '🃏'},
        {'slug': 'speed_type',   'name': 'Speed Typing',      'min_plan_level': 7, 'reward_per_win_kes': 250, 'icon': '⌨️'},
        {'slug': 'vip_challenge','name': 'VIP Challenge',     'min_plan_level': 8, 'reward_per_win_kes': 500, 'icon': '👑'},
    ]

    for g in GAMES:
        usd = round(g['reward_per_win_kes'] / settings.KES_TO_USD_RATE, 2)
        Game.objects.get_or_create(
            slug=g['slug'],
            defaults={**g, 'reward_per_win_usd': Decimal(str(usd))}
        )
    return {'seeded': len(GAMES)}
