from django.core.management.base import BaseCommand
from django.conf import settings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed initial games, wheel config, and writing categories'

    def handle(self, *args, **options):
        self._seed_games()
        self._seed_wheel()
        self._seed_categories()
        self.stdout.write(self.style.SUCCESS('All seed data created successfully.'))

    def _seed_games(self):
        from apps.games.models import Game
        GAMES = [
            {'slug': 'quiz',          'name': 'Daily Quiz',      'min_plan_level': 1, 'reward_per_win_kes': 50,  'icon': '🧠', 'description': 'Answer 10 questions correctly to win.', 'instructions': 'Pick the correct answer for each question. Score 60% or more to win.'},
            {'slug': 'trivia',        'name': 'Trivia Challenge', 'min_plan_level': 2, 'reward_per_win_kes': 80,  'icon': '❓', 'description': 'Daily trivia across multiple topics.', 'instructions': 'Answer trivia questions. New set every day.'},
            {'slug': 'word_puzzle',   'name': 'Word Puzzle',      'min_plan_level': 3, 'reward_per_win_kes': 100, 'icon': '🔤', 'description': 'Unscramble the hidden word.', 'instructions': 'Rearrange the scrambled letters to find the correct word.'},
            {'slug': 'slots',         'name': 'Slots Machine',    'min_plan_level': 4, 'reward_per_win_kes': 150, 'icon': '🎰', 'description': 'Spin the slots for a 50/50 win.', 'instructions': 'Press spin. Match symbols to win.'},
            {'slug': 'number_match',  'name': 'Number Match',     'min_plan_level': 5, 'reward_per_win_kes': 120, 'icon': '🔢', 'description': 'Match all number pairs on the grid.', 'instructions': 'Flip cards to find matching number pairs.'},
            {'slug': 'memory',        'name': 'Memory Game',      'min_plan_level': 6, 'reward_per_win_kes': 200, 'icon': '🃏', 'description': 'Find all emoji pairs from memory.', 'instructions': 'Flip two cards at a time. Match all pairs to win.'},
            {'slug': 'speed_type',    'name': 'Speed Typing',     'min_plan_level': 7, 'reward_per_win_kes': 250, 'icon': '⌨️', 'description': 'Type as fast as you can.', 'instructions': 'Type the displayed text as accurately and quickly as possible. Score based on WPM.'},
            {'slug': 'vip_challenge', 'name': 'VIP Challenge',    'min_plan_level': 8, 'reward_per_win_kes': 500, 'icon': '👑', 'description': 'Exclusive high-reward challenge for elite members.', 'instructions': 'Complete the elite challenge tasks to earn maximum rewards.'},
        ]
        count = 0
        for g in GAMES:
            usd = round(g['reward_per_win_kes'] / settings.KES_TO_USD_RATE, 4)
            _, created = __import__('apps.games.models', fromlist=['Game']).Game.objects.get_or_create(
                slug=g['slug'],
                defaults={**g, 'reward_per_win_usd': Decimal(str(usd))}
            )
            if created:
                count += 1
        self.stdout.write(f'  Games: {count} created')

    def _seed_wheel(self):
        from apps.wheel.tasks import seed_wheel
        result = seed_wheel()
        self.stdout.write(f'  Wheel: {result}')

    def _seed_categories(self):
        from apps.writing.models import Category
        from django.utils.text import slugify
        CATEGORIES = [
            ('Technology', 'tech', '💻'),
            ('Business', 'business', '📊'),
            ('Health & Wellness', 'health', '🏥'),
            ('Education', 'education', '📚'),
            ('Travel', 'travel', '✈️'),
            ('Finance', 'finance', '💰'),
            ('Lifestyle', 'lifestyle', '🌟'),
            ('Sports', 'sports', '⚽'),
            ('Entertainment', 'entertainment', '🎬'),
            ('Academic', 'academic', '🎓'),
        ]
        count = 0
        for name, slug, icon in CATEGORIES:
            _, created = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'icon': icon, 'is_active': True}
            )
            if created:
                count += 1
        self.stdout.write(f'  Writing categories: {count} created')
