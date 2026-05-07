import secrets
import random
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.db import transaction as db_transaction
from django.db.models import Sum
from datetime import timedelta
from rest_framework import generics, serializers, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Game, GameSession, QuizQuestion, GameLeaderboard
from apps.core.models import generate_transaction_code
from apps.users.models import Transaction, AccountWallet
import logging

logger = logging.getLogger(__name__)


# ── Serializers ──

class GameSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.SerializerMethodField()
    reward_per_win_usd = serializers.ReadOnlyField()

    class Meta:
        model = Game
        fields = [
            'id', 'slug', 'name', 'description', 'instructions',
            'min_plan_level', 'reward_per_win_kes', 'reward_per_win_usd',
            'is_active', 'icon', 'is_unlocked',
        ]

    def get_is_unlocked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        user_plan = request.user.user_plans.filter(
            plan__category='GAMING', status='ACTIVE'
        ).select_related('plan').first()
        if not user_plan:
            return False
        return obj.slug in user_plan.plan.gaming_games_unlocked


class GameSessionSerializer(serializers.ModelSerializer):
    game_name = serializers.CharField(source='game.name', read_only=True)

    class Meta:
        model = GameSession
        fields = [
            'id', 'game_name', 'status', 'score', 'max_score',
            'reward_earned_usd', 'reward_credited',
            'transaction_code', 'created_at',
        ]


class LeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = GameLeaderboard
        fields = ['rank', 'username', 'total_score', 'sessions_played', 'total_earned_usd']


# ── Helpers ──

def get_gaming_plan(user):
    return user.user_plans.filter(
        plan__category='GAMING', status='ACTIVE'
    ).select_related('plan').first()


def check_daily_limits(user, user_plan):
    plan = user_plan.plan
    user_plan.reset_daily_counters()

    max_plays = plan.gaming_plays_per_day
    if max_plays != 0 and user_plan.gaming_plays_today >= max_plays:
        return False, f'Daily game limit of {max_plays} plays reached. Come back tomorrow.'

    today = timezone.now().date()
    today_earnings = Transaction.objects.filter(
        user=user,
        source='GAME',
        type='CREDIT',
        status='COMPLETED',
        created_at__date=today,
    ).aggregate(total=Sum('amount_kes'))['total'] or 0

    if today_earnings >= plan.gaming_max_win_per_day_kes:
        return False, f'Daily earnings cap of KES {plan.gaming_max_win_per_day_kes} reached.'

    return True, ''


# ── Views ──

class GameListView(generics.ListAPIView):
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    queryset = Game.objects.filter(is_active=True)


class StartGameView(APIView):
    permission_classes = [IsAuthenticated]

    @db_transaction.atomic
    def post(self, request, game_slug):
        user = request.user
        user_plan = get_gaming_plan(user)

        if not user_plan:
            return Response({'error': 'You need an active Gaming plan to play.'}, status=403)

        plan = user_plan.plan
        if game_slug not in plan.gaming_games_unlocked:
            return Response({'error': 'This game is not unlocked on your current plan.'}, status=403)

        ok, err = check_daily_limits(user, user_plan)
        if not ok:
            return Response({'error': err}, status=403)

        try:
            game = Game.objects.get(slug=game_slug, is_active=True)
        except Game.DoesNotExist:
            return Response({'error': 'Game not found.'}, status=404)

        GameSession.objects.filter(
            user=user, game=game, status=GameSession.STATUS_ACTIVE
        ).update(status=GameSession.STATUS_EXPIRED)

        session_token = secrets.token_hex(32)
        expires_at = timezone.now() + timedelta(minutes=15)

        session_data = {
            'session_token': session_token,
            'expires_at': expires_at,
            'status': GameSession.STATUS_ACTIVE,
        }

        payload = {}

        if game_slug in ['quiz', 'trivia']:
            questions = list(
                QuizQuestion.objects.filter(game=game, is_active=True).order_by('?')[:10]
            )
            question_ids = [str(q.id) for q in questions]
            correct_answers = {str(q.id): q.correct_option for q in questions}
            session_data['question_ids'] = question_ids
            session_data['correct_answers'] = correct_answers
            session_data['max_score'] = len(questions)

            payload['questions'] = [
                {
                    'id': str(q.id),
                    'question': q.question,
                    'options': {
                        'a': q.option_a, 'b': q.option_b,
                        'c': q.option_c, 'd': q.option_d,
                    },
                }
                for q in questions
            ]

        elif game_slug == 'word_puzzle':
            words = ['NEXCRIBE', 'DIGITAL', 'EARNING', 'TRANSCRIBE', 'PLATFORM',
                     'REFERRAL', 'WALLET', 'COMMISSION', 'WRITING', 'REWARD']
            word = random.choice(words)
            shuffled = list(word)
            random.shuffle(shuffled)
            session_data['correct_answers'] = {'word': word}
            session_data['max_score'] = 1
            payload['scrambled'] = ''.join(shuffled)
            payload['length'] = len(word)

        elif game_slug == 'number_match':
            numbers = random.sample(range(1, 50), 8)
            pairs = numbers + numbers
            random.shuffle(pairs)
            session_data['correct_answers'] = {'pairs': numbers}
            session_data['max_score'] = 8
            payload['grid'] = pairs

        elif game_slug == 'memory':
            emojis = ['*', '#', '@', '!', '$', '%', '&', '?']
            pairs = emojis + emojis
            random.shuffle(pairs)
            session_data['correct_answers'] = {'pairs': emojis}
            session_data['max_score'] = 8
            payload['grid_size'] = 16

        elif game_slug in ['slots', 'speed_type', 'vip_challenge']:
            session_data['max_score'] = 100
            payload['hint'] = f'Play {game.name} and submit your result.'

        session = GameSession.objects.create(user=user, game=game, **session_data)

        user_plan.gaming_plays_today += 1
        user_plan.save(update_fields=['gaming_plays_today', 'updated_at'])

        return Response({
            'session_id': str(session.id),
            'session_token': session_token,
            'game': game.slug,
            'expires_at': expires_at.isoformat(),
            **payload,
        })


class SubmitGameResultView(APIView):
    permission_classes = [IsAuthenticated]

    @db_transaction.atomic
    def post(self, request, session_id):
        user = request.user
        try:
            session = GameSession.objects.select_for_update().get(
                id=session_id, user=user, status=GameSession.STATUS_ACTIVE
            )
        except GameSession.DoesNotExist:
            return Response({'error': 'Session not found or already completed.'}, status=404)

        if session.expires_at and timezone.now() > session.expires_at:
            session.status = GameSession.STATUS_EXPIRED
            session.save()
            return Response({'error': 'Session expired.'}, status=400)

        token = request.data.get('session_token')
        if token != session.session_token:
            return Response({'error': 'Invalid session token.'}, status=403)

        game = session.game
        answers = request.data.get('answers', {})
        score = 0
        correct = session.correct_answers

        if game.slug in ['quiz', 'trivia']:
            for qid in session.question_ids:
                if answers.get(qid) == correct.get(qid):
                    score += 1
            max_score = len(session.question_ids)

        elif game.slug == 'word_puzzle':
            submitted = answers.get('word', '').upper().strip()
            score = 1 if submitted == correct.get('word') else 0
            max_score = 1

        elif game.slug in ['number_match', 'memory']:
            score = min(int(answers.get('matches', 0)), session.max_score)
            max_score = session.max_score

        elif game.slug == 'slots':
            won = random.random() < 0.50
            score = 100 if won else 0
            max_score = 100

        elif game.slug == 'speed_type':
            wpm = int(answers.get('wpm', 0))
            score = min(wpm, 100)
            max_score = 100

        elif game.slug == 'vip_challenge':
            score = min(int(answers.get('score', 0)), 100)
            max_score = 100
        else:
            score = 0
            max_score = 100

        won = (score / max(max_score, 1)) >= 0.60
        reward_kes = Decimal(str(game.reward_per_win_kes)) if won else Decimal('0')
        reward_usd = Decimal(str(game.reward_per_win_usd)) if won else Decimal('0')

        # Check daily earnings cap
        user_plan = get_gaming_plan(user)
        if user_plan and won:
            today = timezone.now().date()
            today_kes = Transaction.objects.filter(
                user=user, source='GAME', type='CREDIT',
                status='COMPLETED', created_at__date=today
            ).aggregate(total=Sum('amount_kes'))['total'] or 0

            cap = Decimal(str(user_plan.plan.gaming_max_win_per_day_kes))
            if Decimal(str(today_kes)) + reward_kes > cap:
                reward_kes = max(cap - Decimal(str(today_kes)), Decimal('0'))
                reward_usd = (reward_kes / Decimal(str(settings.KES_TO_USD_RATE))).quantize(Decimal('0.01'))

        session.status = GameSession.STATUS_COMPLETED
        session.score = score
        session.max_score = max_score
        session.reward_earned_kes = reward_kes
        session.reward_earned_usd = reward_usd

        if reward_usd > 0:
            txn_code = generate_transaction_code()
            session.transaction_code = txn_code
            session.reward_credited = True

            # select_for_update fetches fresh from DB, avoids stale cached instance
            wallet = AccountWallet.objects.select_for_update().get(user=user)
            wallet.balance_usd += reward_usd
            wallet.total_earned_usd += reward_usd
            wallet.save(update_fields=['balance_usd', 'total_earned_usd', 'updated_at'])

            Transaction.objects.create(
                user=user,
                transaction_code=txn_code,
                wallet_type='ACCOUNT',
                type='CREDIT',
                amount_usd=reward_usd,
                amount_kes=reward_kes,
                source='GAME',
                description=f'Game reward: {game.name} (score {score}/{max_score})',
                status='COMPLETED',
                balance_after_usd=wallet.balance_usd,
            )

            today = timezone.now().date()
            lb, _ = GameLeaderboard.objects.get_or_create(
                game=game, user=user, date=today,
                defaults={'total_score': 0, 'sessions_played': 0, 'total_earned_usd': 0}
            )
            lb.total_score += score
            lb.sessions_played += 1
            lb.total_earned_usd += reward_usd
            lb.save()

            try:
                from apps.notifications.utils import create_notification
                create_notification(
                    user, 'GAME_REWARD',
                    f'Game Win: +${reward_usd}',
                    f'You won ${reward_usd} playing {game.name}! '
                    f'Score: {score}/{max_score}. Txn: {txn_code}',
                    '/dashboard/wallet',
                )
            except Exception as e:
                logger.warning(f'Notification failed: {e}')

            if reward_usd >= Decimal('0.50'):
                try:
                    from apps.notifications.utils import send_html_email
                    send_html_email(
                        user=user,
                        email_type='GAME_REWARD',
                        subject=f'You won ${reward_usd} playing {game.name}!',
                        template_name='game_reward.html',
                        context={
                            'game_name': game.name,
                            'amount_usd': str(reward_usd),
                            'txn_code': txn_code,
                        },
                    )
                except Exception as e:
                    logger.warning(f'Game reward email failed: {e}')

        session.save()

        return Response({
            'result': 'win' if won else 'loss',
            'score': score,
            'max_score': max_score,
            'percentage': round((score / max(max_score, 1)) * 100),
            'reward_usd': str(reward_usd),
            'reward_kes': str(reward_kes),
            'transaction_code': session.transaction_code or None,
        })


class MyGameHistoryView(generics.ListAPIView):
    serializer_class = GameSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GameSession.objects.filter(
            user=self.request.user,
            status=GameSession.STATUS_COMPLETED,
        ).select_related('game').order_by('-created_at')[:50]


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, game_slug):
        today = timezone.now().date()
        entries = GameLeaderboard.objects.filter(
            game__slug=game_slug, date=today
        ).select_related('user').order_by('-total_score')[:20]

        ranked = []
        for i, entry in enumerate(entries, 1):
            entry.rank = i
            ranked.append(LeaderboardSerializer(entry).data)

        return Response({'date': str(today), 'leaderboard': ranked})


class AdminGameStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.db.models import Count
        stats = GameSession.objects.filter(
            status=GameSession.STATUS_COMPLETED
        ).values('game__name').annotate(
            sessions=Count('id'),
            total_paid=Sum('reward_earned_usd'),
        ).order_by('-sessions')
        return Response({'game_stats': list(stats)})