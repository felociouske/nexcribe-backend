import random
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from django.db import transaction as db_transaction
from rest_framework import generics, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import WheelConfig, WheelSlice, SpinResult
from apps.core.models import generate_transaction_code
from apps.users.models import Transaction, AccountWallet
import logging

logger = logging.getLogger(__name__)


class WheelSliceSerializer(serializers.ModelSerializer):
    reward_value_usd = serializers.ReadOnlyField()

    class Meta:
        model = WheelSlice
        fields = [
            'id', 'label', 'reward_type', 'reward_value_kes',
            'reward_value_usd', 'reward_spins', 'color_hex', 'display_order',
        ]


class WheelConfigSerializer(serializers.ModelSerializer):
    slices = WheelSliceSerializer(many=True, read_only=True)

    class Meta:
        model = WheelConfig
        fields = ['id', 'name', 'description', 'slices']


class SpinResultSerializer(serializers.ModelSerializer):
    slice_label = serializers.CharField(source='slice_won.label', read_only=True)
    slice_color = serializers.CharField(source='slice_won.color_hex', read_only=True)

    class Meta:
        model = SpinResult
        fields = [
            'id', 'slice_label', 'slice_color', 'reward_type',
            'reward_kes', 'reward_usd', 'bonus_spins',
            'transaction_code', 'credited', 'created_at',
        ]


def weighted_spin(slices):
    population = list(slices)
    weights = [float(s.probability) for s in population]
    total = sum(weights)
    if total == 0:
        return random.choice(population)
    weights = [w / total for w in weights]
    return random.choices(population, weights=weights, k=1)[0]


class WheelConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wheel = WheelConfig.objects.filter(is_active=True).prefetch_related('slices').first()
        if not wheel:
            return Response({'error': 'No active wheel configured.'}, status=404)
        return Response(WheelConfigSerializer(wheel).data)


class SpinWheelView(APIView):
    permission_classes = [IsAuthenticated]

    @db_transaction.atomic
    def post(self, request):
        user = request.user

        user_plan = user.user_plans.filter(
            plan__category='GAMING', status='ACTIVE'
        ).select_related('plan').first()

        if not user_plan:
            return Response(
                {'error': 'You need an active Gaming plan to spin.'}, status=403
            )

        user_plan.reset_daily_counters()
        plan = user_plan.plan
        max_spins = plan.gaming_wheel_spins_per_day

        if max_spins != 0 and user_plan.wheel_spins_today >= max_spins:
            return Response(
                {'error': f'Daily spin limit of {max_spins} reached. Come back tomorrow.'},
                status=403
            )

        wheel = WheelConfig.objects.filter(is_active=True).prefetch_related('slices').first()
        if not wheel:
            return Response({'error': 'Wheel not configured.'}, status=500)

        slices = list(wheel.slices.all())
        if not slices:
            return Response({'error': 'Wheel has no slices.'}, status=500)

        winning_slice = weighted_spin(slices)

        reward_kes = Decimal('0')
        reward_usd = Decimal('0')
        bonus_spins = 0
        txn_code = ''
        credited = False

        if winning_slice.reward_type == WheelSlice.REWARD_CASH and winning_slice.reward_value_kes > 0:
            reward_kes = Decimal(str(winning_slice.reward_value_kes))
            reward_usd = Decimal(str(winning_slice.reward_value_usd))
            txn_code = generate_transaction_code()
            credited = True

            # select_for_update fetches fresh from DB — prevents stale cached wallet balance
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
                source='WHEEL',
                description=f'Lucky wheel win: {winning_slice.label}',
                status='COMPLETED',
                balance_after_usd=wallet.balance_usd,
            )

            try:
                from apps.notifications.utils import create_notification
                create_notification(
                    user, 'SPIN_WIN',
                    f'Wheel Win: +${reward_usd}',
                    f'You landed on "{winning_slice.label}" and won ${reward_usd}! '
                    f'Credited to your Account Wallet. Txn: {txn_code}',
                    '/dashboard/wallet',
                )
            except Exception as e:
                logger.warning(f'Wheel notification failed: {e}')

            if reward_usd >= Decimal('0.50'):
                try:
                    from apps.notifications.tasks import send_spin_win_email
                    send_spin_win_email.delay(
                        str(user.id), winning_slice.label, str(reward_usd), txn_code
                    )
                except Exception as e:
                    logger.warning(f'Spin win email failed: {e}')

        elif winning_slice.reward_type == WheelSlice.REWARD_SPINS and winning_slice.reward_spins > 0:
            bonus_spins = winning_slice.reward_spins
            credited = True

        user_plan.wheel_spins_today += 1
        user_plan.save(update_fields=['wheel_spins_today', 'updated_at'])

        SpinResult.objects.create(
            user=user,
            wheel=wheel,
            slice_won=winning_slice,
            reward_type=winning_slice.reward_type,
            reward_kes=reward_kes,
            reward_usd=reward_usd,
            bonus_spins=bonus_spins,
            transaction_code=txn_code,
            credited=credited,
        )

        spins_left = (
            max_spins - user_plan.wheel_spins_today
            if max_spins != 0 else 'unlimited'
        )

        return Response({
            'winning_slice_id': str(winning_slice.id),
            'winning_slice_label': winning_slice.label,
            'reward_type': winning_slice.reward_type,
            'reward_usd': str(reward_usd),
            'reward_kes': str(reward_kes),
            'bonus_spins': bonus_spins,
            'transaction_code': txn_code or None,
            'spins_remaining': spins_left,
        })


class SpinHistoryView(generics.ListAPIView):
    serializer_class = SpinResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SpinResult.objects.filter(
            user=self.request.user
        ).select_related('slice_won').order_by('-created_at')[:50]