from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from decimal import Decimal
import logging
from django.db import transaction
from .models import Plan, UserPlan, CATEGORY_CHOICES
from .serializers import PlanSerializer, UserPlanSerializer
from apps.users.models import Transaction, DepositWallet
from apps.core.models import generate_transaction_code

logger = logging.getLogger(__name__)


class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Plan.objects.filter(is_active=True)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category.upper())
        return qs.order_by('category', 'level')


class PlanDetailView(generics.RetrieveAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    queryset = Plan.objects.filter(is_active=True)


class MyPlansView(generics.ListAPIView):
    serializer_class = UserPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPlan.objects.filter(
            user=self.request.user,
            status=UserPlan.STATUS_ACTIVE,
        ).select_related('plan')


class PurchasePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, plan_id):
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response({'error': 'Plan not found.'}, status=404)

        user = request.user
        amount_usd = Decimal(str(plan.price_usd))
        amount_kes = Decimal(str(plan.price_kes))
        txn_code = generate_transaction_code()

        try:
            with transaction.atomic():
                deposit_wallet, _ = DepositWallet.objects.select_for_update().get_or_create(
                    user=user
                )

                if Decimal(deposit_wallet.balance_usd) < amount_usd:
                    return Response({
                        'error': (
                            f'Insufficient funds. This plan costs ${amount_usd}. '
                            f'Your Deposit Wallet has ${deposit_wallet.balance_usd:.2f}. '
                            f'Please deposit more funds.'
                        )
                    }, status=400)

                # Expire previous active plan in the same category
                UserPlan.objects.filter(
                    user=user,
                    plan__category=plan.category,
                    status=UserPlan.STATUS_ACTIVE,
                ).update(status=UserPlan.STATUS_EXPIRED)

                # Deduct from deposit wallet
                deposit_wallet.balance_usd = Decimal(deposit_wallet.balance_usd) - amount_usd
                deposit_wallet.total_spent_usd = Decimal(deposit_wallet.total_spent_usd) + amount_usd
                deposit_wallet.save(update_fields=['balance_usd', 'total_spent_usd', 'updated_at'])

                # Create user plan
                UserPlan.objects.create(
                    user=user,
                    plan=plan,
                    status=UserPlan.STATUS_ACTIVE,
                    transaction_code=txn_code,
                )

                # Transaction record
                Transaction.objects.create(
                    user=user,
                    transaction_code=txn_code,
                    wallet_type='DEPOSIT',
                    type='DEBIT',
                    amount_usd=amount_usd,
                    amount_kes=amount_kes,
                    source='PLAN_PURCHASE',
                    description=f'{plan.get_category_display()} — {plan.name} (Level {plan.level})',
                    status='COMPLETED',
                    balance_after_usd=deposit_wallet.balance_usd,
                )

        except Exception as e:
            logger.error(f'Plan purchase failed: {e}')
            return Response({'error': 'Purchase failed. Please try again.'}, status=500)

        # Affiliate commissions — called directly (no .delay) so it works without Celery
        try:
            from apps.affiliates.tasks import process_affiliate_commissions
            process_affiliate_commissions(
                purchaser_id=str(user.id),
                plan_id=str(plan.id),
                txn_code=txn_code,
            )
        except Exception as e:
            logger.warning(f'Affiliate commission failed (non-critical): {e}')

        # Purchase confirmation email — runs directly, no Celery needed
        try:
            from apps.notifications.tasks import send_plan_purchase_email
            send_plan_purchase_email(str(user.id), str(plan.id), txn_code)
        except Exception as e:
            logger.warning(f'Plan purchase email failed (non-critical): {e}')

        # In-app notification
        try:
            from apps.notifications.utils import create_notification
            create_notification(
                user, 'PLAN_PURCHASE',
                f'{plan.name} Plan Activated',
                f'Your {plan.name} {plan.get_category_display()} plan is now active. Start earning!',
                '/dashboard/plans',
                metadata={'plan_id': str(plan.id), 'txn_code': txn_code},
            )
        except Exception as e:
            logger.warning(f'Notification failed (non-critical): {e}')

        return Response({
            'message': f'{plan.name} activated for {plan.get_category_display()}.',
            'transaction_code': txn_code,
            'deposit_wallet_balance': str(deposit_wallet.balance_usd),
            'plan': PlanSerializer(plan).data,
        }, status=201)


class CategorySummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response([
            {'value': k, 'label': v} for k, v in CATEGORY_CHOICES
        ])