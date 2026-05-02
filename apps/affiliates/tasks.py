from celery import shared_task
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_affiliate_commissions(self, purchaser_id, plan_id, txn_code):
    """
    Walk up the affiliate tree up to 4 levels and credit commissions:
    L1=60%, L2=15%, L3=5%, L4=3%
    """
    try:
        from apps.users.models import User, Transaction, YieldsWallet
        from apps.plans.models import Plan
        from apps.affiliates.models import (
            AffiliateNode, Commission,
            COMMISSION_RATES, MAX_COMMISSION_LEVELS,
        )
        from apps.core.models import generate_transaction_code

        purchaser = User.objects.get(id=purchaser_id)
        plan = Plan.objects.get(id=plan_id)

        try:
            node = AffiliateNode.objects.get(user=purchaser)
        except AffiliateNode.DoesNotExist:
            logger.info(f'No affiliate node for {purchaser.email} — skipping commissions')
            return {'status': 'no_node'}

        ancestors = node.get_ancestors(max_levels=MAX_COMMISSION_LEVELS)
        if not ancestors:
            logger.info(f'No ancestors for {purchaser.email} — no commissions to pay')
            return {'status': 'no_ancestors'}

        plan_price_kes = Decimal(str(plan.price_kes))
        kes_rate = Decimal(str(settings.KES_TO_USD_RATE))
        commissions_created = []

        for depth_index, ancestor_node in enumerate(ancestors, start=1):
            rate = Decimal(str(COMMISSION_RATES.get(depth_index, 0)))
            if rate == 0:
                break

            try:
                amount_kes = (plan_price_kes * rate).quantize(Decimal('0.01'))
                amount_usd = (amount_kes / kes_rate).quantize(Decimal('0.0001'))
                comm_txn_code = generate_transaction_code()

                Commission.objects.create(
                    recipient=ancestor_node.user,
                    from_user=purchaser,
                    plan=plan,
                    level_depth=depth_index,
                    rate=rate,
                    plan_price_kes=plan_price_kes,
                    amount_kes=amount_kes,
                    amount_usd=amount_usd,
                    status=Commission.STATUS_PAID,
                    transaction_code=comm_txn_code,
                    plan_purchase_txn=txn_code,
                    paid_at=timezone.now(),
                )

                wallet, _ = YieldsWallet.objects.get_or_create(user=ancestor_node.user)
                wallet.balance_usd += amount_usd
                wallet.total_earned_usd += amount_usd
                wallet.save(update_fields=['balance_usd', 'total_earned_usd', 'updated_at'])

                Transaction.objects.create(
                    user=ancestor_node.user,
                    transaction_code=comm_txn_code,
                    wallet_type='YIELDS',
                    type='CREDIT',
                    amount_usd=amount_usd,
                    amount_kes=amount_kes,
                    source='REFERRAL',
                    description=(
                        f'L{depth_index} commission ({int(rate * 100)}%) — '
                        f'{purchaser.username} purchased {plan.name}'
                    ),
                    status='COMPLETED',
                    balance_after_usd=wallet.balance_usd,
                )

                commissions_created.append({
                    'recipient': ancestor_node.user.email,
                    'level': depth_index,
                    'rate': f'{int(rate * 100)}%',
                    'amount_usd': str(amount_usd),
                })

                logger.info(
                    f'Commission L{depth_index} ({int(rate*100)}%): '
                    f'KES {amount_kes} to {ancestor_node.user.email}'
                )

                # Synchronous in-app notification
                try:
                    from apps.notifications.utils import create_notification
                    create_notification(
                        ancestor_node.user, 'COMMISSION',
                        f'Level {depth_index} Commission — +KES {amount_kes}',
                        (
                            f'{int(rate * 100)}% commission: {purchaser.username} '
                            f'purchased {plan.name}. '
                            f'KES {amount_kes} credited to your Yields Wallet.'
                        ),
                        '/dashboard/wallet',
                        metadata={
                            'amount_usd': str(amount_usd),
                            'amount_kes': str(amount_kes),
                            'txn_code': comm_txn_code,
                            'level': depth_index,
                        },
                    )
                except Exception as e:
                    logger.warning(f'Commission notification failed at L{depth_index}: {e}')

                # Email — use .delay() to queue via Celery
                try:
                    from apps.notifications.tasks import send_commission_email
                    send_commission_email.delay(
                        str(ancestor_node.user.id),
                        str(amount_usd),
                        purchaser.username,
                        plan.name,
                        depth_index,
                        comm_txn_code,
                    )
                except Exception as e:
                    logger.warning(f'Commission email failed at L{depth_index}: {e}')

            except Exception as e:
                logger.error(
                    f'Failed commission at L{depth_index} for '
                    f'{ancestor_node.user.email}: {e}'
                )
                continue

        logger.info(
            f'Commissions complete: {len(commissions_created)} paid for {purchaser.email}'
        )
        return {'status': 'success', 'commissions': commissions_created}

    except Exception as exc:
        logger.error(f'process_affiliate_commissions failed: {exc}')
        if getattr(self, 'request', None) and getattr(self.request, 'id', None):
            raise self.retry(exc=exc, countdown=60)
        raise