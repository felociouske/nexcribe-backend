from django.core.management.base import BaseCommand
from apps.plans.models import Plan, CATEGORY_WRITING, CATEGORY_TRANSCRIPTION, CATEGORY_GAMING


# ── Writing Plans — 8 levels ──
# Prices:  1,550 / 2,400 / 3,600 / 4,900 / 5,500 / 6,500 / 8,000 / 9,500
#
# task_total × pay_per_task = total possible earnings on this plan
# Target: total earnings = ~1.8× the plan price (80% return)
# e.g. L1: 3 tasks × KES 900 = KES 2,700 on a KES 1,550 plan → 74% profit
#
WRITING_PLANS = [
    {
        'level': 1, 'name': 'Starter Scribe', 'price_kes': 1550,
        'writing_tasks_per_month': 3,               # 3 tasks total on this plan
        'writing_max_pay_per_task_kes': 900,        # up to KES 900 per task
        'writing_revisions_per_task': 0,
        'writing_priority_queue': False,
        'writing_direct_assignments': False,
        'description': 'Begin your writing journey. 3 tasks, earn up to KES 900 each.',
        'features_list': [
            '3 writing tasks (lifetime)',
            'Earn up to KES 900 per task',
            'Total potential: KES 2,700',
            'Basic article types',
        ],
    },
    {
        'level': 2, 'name': 'Advanced Starter', 'price_kes': 2400,
        'writing_tasks_per_month': 5,
        'writing_max_pay_per_task_kes': 900,
        'writing_revisions_per_task': 1,
        'writing_priority_queue': False,
        'writing_direct_assignments': False,
        'description': '5 tasks with blog and academic content access.',
        'features_list': [
            '5 writing tasks (lifetime)',
            'Earn up to KES 900 per task',
            'Total potential: KES 4,500',
            'Blog + academic content',
            '1 revision per task',
        ],
    },
    {
        'level': 3, 'name': 'Verse Writer', 'price_kes': 3600,
        'writing_tasks_per_month': 7,
        'writing_max_pay_per_task_kes': 1000,
        'writing_revisions_per_task': 2,
        'writing_priority_queue': False,
        'writing_direct_assignments': False,
        'description': '7 tasks across all content types.',
        'features_list': [
            '7 writing tasks (lifetime)',
            'Earn up to KES 1,000 per task',
            'Total potential: KES 7,000',
            'All content types',
            '2 revisions per task',
        ],
    },
    {
        'level': 4, 'name': 'Folio Writer', 'price_kes': 4900,
        'writing_tasks_per_month': 9,
        'writing_max_pay_per_task_kes': 1100,
        'writing_revisions_per_task': 3,
        'writing_priority_queue': True,
        'writing_direct_assignments': False,
        'description': '9 tasks with priority queue access.',
        'features_list': [
            '9 writing tasks (lifetime)',
            'Earn up to KES 1,100 per task',
            'Total potential: KES 9,900',
            'Priority task queue',
            '3 revisions per task',
        ],
    },
    {
        'level': 5, 'name': 'Codex Pro', 'price_kes': 5500,
        'writing_tasks_per_month': 10,
        'writing_max_pay_per_task_kes': 1100,
        'writing_revisions_per_task': 99,
        'writing_priority_queue': True,
        'writing_direct_assignments': False,
        'description': '10 tasks, unlimited revisions and featured writer status.',
        'features_list': [
            '10 writing tasks (lifetime)',
            'Earn up to KES 1,100 per task',
            'Total potential: KES 11,000',
            'Priority + featured writer',
            'Unlimited revisions',
        ],
    },
    {
        'level': 6, 'name': 'Scroll Elite', 'price_kes': 6500,
        'writing_tasks_per_month': 12,
        'writing_max_pay_per_task_kes': 1100,
        'writing_revisions_per_task': 99,
        'writing_priority_queue': True,
        'writing_direct_assignments': False,
        'description': '12 premium client tasks.',
        'features_list': [
            '12 writing tasks (lifetime)',
            'Earn up to KES 1,100 per task',
            'Total potential: KES 13,200',
            'Premium client pool',
            'Unlimited revisions',
        ],
    },
    {
        'level': 7, 'name': 'Atlas Master', 'price_kes': 8000,
        'writing_tasks_per_month': 15,
        'writing_max_pay_per_task_kes': 1200,
        'writing_revisions_per_task': 99,
        'writing_priority_queue': True,
        'writing_direct_assignments': True,
        'description': '15 VIP client tasks with dedicated support.',
        'features_list': [
            '15 writing tasks (lifetime)',
            'Earn up to KES 1,200 per task',
            'Total potential: KES 18,000',
            'VIP client pool',
            'Direct assignments + dedicated support',
        ],
    },
    {
        'level': 8, 'name': 'Nexus Legend', 'price_kes': 9500,
        'writing_tasks_per_month': 20,
        'writing_max_pay_per_task_kes': 1200,
        'writing_revisions_per_task': 99,
        'writing_priority_queue': True,
        'writing_direct_assignments': True,
        'description': '20 elite tasks, revenue-share, and top-tier client access.',
        'features_list': [
            '20 writing tasks (lifetime)',
            'Earn up to KES 1,200 per task',
            'Total potential: KES 24,000',
            'Elite client pool',
            'Revenue share bonus',
        ],
    },
]


# ── Transcription Plans — 6 levels ──
# Prices: 1,700 / 2,500 / 3,900 / 4,900 / 6,700 / 9,500
TRANSCRIPTION_PLANS = [
    {
        'level': 1, 'name': 'Starter Listener', 'price_kes': 1700,
        'transcription_tasks_per_month': 4,         # 4 tasks total
        'transcription_max_audio_minutes': 9999,
        'transcription_max_pay_per_task_kes': 900,
        'transcription_difficulty_access': 'BASIC',
        'transcription_priority_queue': False,
        'description': '4 basic audio tasks. Earn KES 900 per approved transcript.',
        'features_list': [
            '4 audio tasks (lifetime)',
            'Earn up to KES 900 per task',
            'Total potential: KES 3,600',
            'Basic difficulty audio',
        ],
    },
    {
        'level': 2, 'name': 'Advanced Listener', 'price_kes': 2500,
        'transcription_tasks_per_month': 6,
        'transcription_max_audio_minutes': 9999,
        'transcription_max_pay_per_task_kes': 900,
        'transcription_difficulty_access': 'EASY',
        'transcription_priority_queue': False,
        'description': '6 easy-difficulty audio tasks.',
        'features_list': [
            '6 audio tasks (lifetime)',
            'Earn up to KES 900 per task',
            'Total potential: KES 5,400',
            'Basic + easy difficulty',
        ],
    },
    {
        'level': 3, 'name': 'Verse Transcriber', 'price_kes': 5500,
        'transcription_tasks_per_month': 8,
        'transcription_max_audio_minutes': 9999,
        'transcription_max_pay_per_task_kes': 4000,
        'transcription_difficulty_access': 'MEDIUM',
        'transcription_priority_queue': False,
        'description': '8 tasks up to medium difficulty.',
        'features_list': [
            '8 audio tasks (lifetime)',
            'Earn up to KES 1,000 per task',
            'Total potential: KES 8,000',
            'Up to medium difficulty',
        ],
    },
    {
        'level': 4, 'name': 'Folio Transcriber', 'price_kes': 8000,
        'transcription_tasks_per_month': 10,
        'transcription_max_audio_minutes': 9999,
        'transcription_max_pay_per_task_kes': 6000,
        'transcription_difficulty_access': 'ALL',
        'transcription_priority_queue': True,
        'description': '10 tasks across all difficulty levels with priority queue.',
        'features_list': [
            '10 audio tasks (lifetime)',
            'Earn up to KES 1,000 per task',
            'Total potential: KES 10,000',
            'All difficulty levels',
            'Priority task queue',
        ],
    },
    {
        'level': 5, 'name': 'Codex Transcriber', 'price_kes': 26000,
        'transcription_tasks_per_month': 14,
        'transcription_max_audio_minutes': 9999,
        'transcription_max_pay_per_task_kes': 10000,
        'transcription_difficulty_access': 'ALL',
        'transcription_priority_queue': True,
        'description': '14 tasks including multi-speaker and accented audio.',
        'features_list': [
            '14 audio tasks (lifetime)',
            'Earn up to KES 1,000 per task',
            'Total potential: KES 14,000',
            'Multi-speaker audio',
            'Priority queue',
        ],
    },
    {
        'level': 6, 'name': 'Nexus Transcriber', 'price_kes': 41000,
        'transcription_tasks_per_month': 20,
        'transcription_max_audio_minutes': 9999,
        'transcription_max_pay_per_task_kes': 1000,
        'transcription_difficulty_access': 'ALL',
        'transcription_priority_queue': True,
        'description': '20 elite tasks including legal and medical content.',
        'features_list': [
            '20 audio tasks (lifetime)',
            'Earn up to KES 1,000 per task',
            'Total potential: KES 20,000',
            'Legal + medical content',
            'Rush task access',
        ],
    },
]


# ── Gaming Plans — 6 levels ──
# Prices: 2,400 / 3,600 / 4,900 / 10,000 / 24,000 / 50,000
# Gaming works differently — daily play limits reset each day.
# Earnings are daily: daily_cap × days played.
GAMING_PLANS = [
    {
        'level': 1, 'name': 'Starter Gamer', 'price_kes': 2400,
        'gaming_plays_per_day': 5,
        'gaming_max_win_per_day_kes': 500,
        'gaming_wheel_spins_per_day': 2,
        'gaming_games_unlocked': ['quiz'],
        'gaming_leaderboard_bonus': False,
        'gaming_tournament_access': False,
        'description': '5 plays and 2 spins daily. Win up to KES 500 per day.',
        'features_list': [
            '5 game plays per day',
            '2 wheel spins per day',
            'Win up to KES 500/day',
            'Quiz game unlocked',
        ],
    },
    {
        'level': 2, 'name': 'Advanced Gamer', 'price_kes': 3600,
        'gaming_plays_per_day': 10,
        'gaming_max_win_per_day_kes': 800,
        'gaming_wheel_spins_per_day': 4,
        'gaming_games_unlocked': ['quiz', 'trivia'],
        'gaming_leaderboard_bonus': False,
        'gaming_tournament_access': False,
        'description': '10 plays and 4 spins daily. Trivia unlocked.',
        'features_list': [
            '10 game plays per day',
            '4 wheel spins per day',
            'Win up to KES 800/day',
            'Trivia game unlocked',
        ],
    },
    {
        'level': 3, 'name': 'Verse Gamer', 'price_kes': 4900,
        'gaming_plays_per_day': 15,
        'gaming_max_win_per_day_kes': 1100,
        'gaming_wheel_spins_per_day': 6,
        'gaming_games_unlocked': ['quiz', 'trivia', 'word_puzzle'],
        'gaming_leaderboard_bonus': False,
        'gaming_tournament_access': False,
        'description': '15 plays and 6 spins daily. Word puzzle unlocked.',
        'features_list': [
            '15 game plays per day',
            '6 wheel spins per day',
            'Win up to KES 1,100/day',
            'Word puzzle unlocked',
        ],
    },
    {
        'level': 4, 'name': 'Folio Gamer', 'price_kes': 10000,
        'gaming_plays_per_day': 20,
        'gaming_max_win_per_day_kes': 2300,
        'gaming_wheel_spins_per_day': 8,
        'gaming_games_unlocked': ['quiz', 'trivia', 'word_puzzle', 'slots'],
        'gaming_leaderboard_bonus': True,
        'gaming_tournament_access': False,
        'description': '20 plays and 8 spins daily. Slots and leaderboard bonuses.',
        'features_list': [
            '20 game plays per day',
            '8 wheel spins per day',
            'Win up to KES 2,300/day',
            'Slots machine unlocked',
            'Leaderboard bonuses',
        ],
    },
    {
        'level': 5, 'name': 'Codex Gamer', 'price_kes': 24000,
        'gaming_plays_per_day': 30,
        'gaming_max_win_per_day_kes': 5500,
        'gaming_wheel_spins_per_day': 12,
        'gaming_games_unlocked': ['quiz', 'trivia', 'word_puzzle', 'slots', 'number_match', 'memory'],
        'gaming_leaderboard_bonus': True,
        'gaming_tournament_access': True,
        'description': '30 plays and 12 spins daily. Tournament access and 6 games.',
        'features_list': [
            '30 game plays per day',
            '12 wheel spins per day',
            'Win up to KES 5,500/day',
            'Tournament access',
            '6 games unlocked',
        ],
    },
    {
        'level': 6, 'name': 'Nexus Legend', 'price_kes': 50000,
        'gaming_plays_per_day': 0,           # 0 = unlimited
        'gaming_max_win_per_day_kes': 11400,
        'gaming_wheel_spins_per_day': 0,     # 0 = unlimited
        'gaming_games_unlocked': [
            'quiz', 'trivia', 'word_puzzle', 'slots',
            'number_match', 'memory', 'speed_type', 'vip_challenge',
        ],
        'gaming_leaderboard_bonus': True,
        'gaming_tournament_access': True,
        'description': 'Unlimited plays and spins. All games. VIP tournaments.',
        'features_list': [
            'Unlimited game plays per day',
            'Unlimited wheel spins per day',
            'Win up to KES 11,400/day',
            'All 8 games unlocked',
            'VIP tournaments',
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed Nexcribe plans: 8 Writing, 6 Transcription, 6 Gaming'

    def handle(self, *args, **options):
        created = 0
        updated = 0

        all_plans = [
            (CATEGORY_WRITING, WRITING_PLANS),
            (CATEGORY_TRANSCRIPTION, TRANSCRIPTION_PLANS),
            (CATEGORY_GAMING, GAMING_PLANS),
        ]

        for category, plans in all_plans:
            for data in plans:
                data = dict(data)
                features = data.pop('features_list')
                desc = data.pop('description')
                plan, was_created = Plan.objects.update_or_create(
                    category=category,
                    level=data['level'],
                    defaults={
                        **data,
                        'category': category,
                        'description': desc,
                        'features_list': features,
                    }
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        # Remove old level 7 and 8 plans for Transcription and Gaming
        from apps.plans.models import Plan as PlanModel
        removed = PlanModel.objects.filter(
            category__in=[CATEGORY_TRANSCRIPTION, CATEGORY_GAMING],
            level__gt=6
        ).delete()[0]

        self.stdout.write(self.style.SUCCESS(
            f'\nDone!'
            f'\n  Created : {created}'
            f'\n  Updated : {updated}'
            f'\n  Removed : {removed} old plans'
            f'\n'
            f'\n  Writing       : {PlanModel.objects.filter(category=CATEGORY_WRITING).count()} plans'
            f'\n  Transcription : {PlanModel.objects.filter(category=CATEGORY_TRANSCRIPTION).count()} plans'
            f'\n  Gaming        : {PlanModel.objects.filter(category=CATEGORY_GAMING).count()} plans'
        ))