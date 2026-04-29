from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """
    BUG FIX: was `except Exception: pass` — silently swallowed every failure
    with no retry. Now retries up to 3 times with a 30s back-off.
    """
    try:
        from apps.users.models import User
        from .utils import send_html_email
        user = User.objects.get(id=user_id)
        send_html_email(
            user=user,
            email_type='WELCOME',
            subject='Welcome to Nexcribe — Start Earning Today',
            template_name='welcome.html',
            context={
                'username': user.first_name or user.username,
            },
        )
    except Exception as exc:
        logger.error(f'send_welcome_email failed for {user_id}: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id, token):
    try:
        from apps.users.models import User
        from .utils import send_html_email
        from django.conf import settings
        user = User.objects.get(id=user_id)
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        send_html_email(
            user=user,
            email_type='EMAIL_VERIFICATION',
            subject='Verify Your Nexcribe Email Address',
            template_name='verify_email.html',
            context={'verify_url': verify_url},
        )
    except Exception as exc:
        logger.error(f'send_verification_email failed for {user_id}: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, token):
    try:
        from apps.users.models import User
        from .utils import send_html_email
        from django.conf import settings
        user = User.objects.get(id=user_id)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        send_html_email(
            user=user,
            email_type='PASSWORD_RESET',
            subject='Reset Your Nexcribe Password',
            template_name='password_reset.html',
            context={'reset_url': reset_url},
        )
    except Exception as exc:
        logger.error(f'send_password_reset_email failed for {user_id}: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_commission_email(self, user_id, amount_usd, from_username, plan_name, level_depth, txn_code):
    try:
        from apps.users.models import User
        from .utils import send_html_email, create_notification
        from django.conf import settings
        user = User.objects.get(id=user_id)
        amount_kes = float(amount_usd) * settings.KES_TO_USD_RATE

        send_html_email(
            user=user,
            email_type='COMMISSION_EARNED',
            subject=f'You earned ${amount_usd} in referral commission!',
            template_name='commission_earned.html',
            context={
                'amount_usd': amount_usd,
                'amount_kes': f'{amount_kes:.2f}',
                'from_username': from_username,
                'plan_name': plan_name,
                'level_depth': level_depth,
                'txn_code': txn_code,
            },
        )
        create_notification(
            user=user,
            notification_type='COMMISSION',
            title=f'Commission Earned — ${amount_usd}',
            message=f'Level {level_depth} commission from {from_username} purchasing {plan_name}.',
            link='/dashboard/wallet',
            metadata={'amount_usd': amount_usd, 'txn_code': txn_code},
        )
    except Exception as exc:
        logger.error(f'send_commission_email failed for {user_id}: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_plan_purchase_email(self, user_id, plan_id, txn_code):
    try:
        from apps.users.models import User
        from apps.plans.models import Plan
        from .utils import send_html_email, create_notification
        user = User.objects.get(id=user_id)
        plan = Plan.objects.get(id=plan_id)

        send_html_email(
            user=user,
            email_type='PLAN_PURCHASE',
            subject=f'Plan Activated — {plan.get_category_display()} {plan.name}',
            template_name='plan_purchase.html',
            context={
                'plan_name': plan.name,
                'plan_category': plan.get_category_display(),
                'plan_level': plan.level,
                'price_kes': plan.price_kes,
                'price_usd': plan.price_usd,
                'txn_code': txn_code,
                'features': plan.features_list,
            },
        )
        create_notification(
            user=user,
            notification_type='PLAN_PURCHASE',
            title=f'{plan.get_category_display()} {plan.name} Activated',
            message=f'Your {plan.name} plan is now active. Start earning!',
            link=f'/dashboard/{plan.category.lower()}',
            metadata={'plan_id': str(plan.id), 'txn_code': txn_code},
        )
    except Exception as exc:
        logger.error(f'send_plan_purchase_email failed for {user_id}: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_withdrawal_update_email(self, user_id, amount_usd, wallet_type, status, txn_code, reason=''):
    try:
        from apps.users.models import User
        from .utils import send_html_email, create_notification
        from django.conf import settings
        user = User.objects.get(id=user_id)
        amount_kes = float(amount_usd) * settings.KES_TO_USD_RATE
        wallet_label = 'Account Wallet' if wallet_type == 'ACCOUNT' else 'Yields Wallet'

        send_html_email(
            user=user,
            email_type=f'WITHDRAWAL_{status}',
            subject=f'Withdrawal {status.title()} — {txn_code}',
            template_name='withdrawal_update.html',
            context={
                'amount_usd': amount_usd,
                'amount_kes': f'{amount_kes:.2f}',
                'wallet_label': wallet_label,
                'status': status,
                'txn_code': txn_code,
                'reason': reason,
            },
        )
        create_notification(
            user=user,
            notification_type='WITHDRAWAL',
            title=f'Withdrawal {status.title()}',
            message=(
                f'Your withdrawal of ${amount_usd} from {wallet_label} was {status.lower()}.'
                + (f' Reason: {reason}' if reason and status == 'REJECTED' else '')
            ),
            link='/dashboard/wallet',
            metadata={
                'amount_usd': amount_usd,
                'txn_code': txn_code,
                'status': status,
                'admin_note': reason,
            },
        )
    except Exception as exc:
        logger.error(f'send_withdrawal_update_email failed for {user_id}: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_task_update_email(self, user_id, task_type, task_title, status, feedback='', amount_usd=None):
    """Covers writing and transcription task approvals/rejections."""
    try:
        from apps.users.models import User
        from .utils import send_html_email, create_notification
        user = User.objects.get(id=user_id)

        subject = f'{task_type} Task {status.title()} — {task_title[:40]}'
        send_html_email(
            user=user,
            email_type=f'{task_type.upper()}_TASK_{status}',
            subject=subject,
            template_name='task_update.html',
            context={
                'task_type': task_type,
                'task_title': task_title,
                'status': status,
                'feedback': feedback,
                'amount_usd': amount_usd,
            },
        )
        notif_type = 'TASK_APPROVED' if status == 'APPROVED' else 'TASK_REJECTED'
        create_notification(
            user=user,
            notification_type=notif_type,
            title=f'{task_type} Task {status.title()}',
            message=(
                f'"{task_title}" was {status.lower()}.'
                + (f' Earned ${amount_usd}.' if amount_usd else '')
                + (f' Feedback: {feedback}' if feedback and status == 'REJECTED' else '')
            ),
            link=f'/dashboard/{task_type.lower()}',
            metadata={
                'status': status,
                'amount_usd': amount_usd,
                'admin_note': feedback,
            },
        )
    except Exception as exc:
        logger.error(f'send_task_update_email failed for {user_id}: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_game_reward_email(self, user_id, game_name, amount_usd, txn_code):
    try:
        from apps.users.models import User
        from .utils import send_html_email, create_notification
        user = User.objects.get(id=user_id)
        send_html_email(
            user=user,
            email_type='GAME_REWARD',
            subject=f'You won ${amount_usd} playing {game_name}!',
            template_name='game_reward.html',
            context={'game_name': game_name, 'amount_usd': amount_usd, 'txn_code': txn_code},
        )
        create_notification(
            user=user,
            notification_type='GAME_REWARD',
            title=f'Game Reward — ${amount_usd}',
            message=f'You earned ${amount_usd} from {game_name}.',
            link='/dashboard/games',
            metadata={'amount_usd': amount_usd, 'txn_code': txn_code},
        )
    except Exception as exc:
        logger.error(f'send_game_reward_email failed for {user_id}: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def send_spin_win_email(self, user_id, prize_label, amount_usd, txn_code):
    try:
        from apps.users.models import User
        from .utils import send_html_email, create_notification
        user = User.objects.get(id=user_id)
        send_html_email(
            user=user,
            email_type='SPIN_WIN',
            subject=f'Lucky Wheel Win — {prize_label}!',
            template_name='spin_win.html',
            context={'prize_label': prize_label, 'amount_usd': amount_usd, 'txn_code': txn_code},
        )
        create_notification(
            user=user,
            notification_type='SPIN_WIN',
            title=f'Wheel Win — {prize_label}',
            message=f'You won {prize_label} from the lucky wheel!',
            link='/dashboard/wheel',
            metadata={'amount_usd': amount_usd, 'txn_code': txn_code},
        )
    except Exception as exc:
        logger.error(f'send_spin_win_email failed for {user_id}: {exc}')
        raise self.retry(exc=exc, countdown=30)


@shared_task
def send_weekly_summary():
    """Every Monday 8 AM — send earnings summary to all active users."""
    from apps.users.models import User, Transaction, AccountWallet, YieldsWallet
    from .utils import send_html_email
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum

    week_ago = timezone.now() - timedelta(days=7)
    users = User.objects.filter(is_active=True, is_verified=True)

    sent = 0
    failed = 0

    for user in users:
        try:
            week_txns = Transaction.objects.filter(
                user=user, type='CREDIT',
                created_at__gte=week_ago, status='COMPLETED'
            )
            total = week_txns.aggregate(total=Sum('amount_usd'))['total'] or 0

            # BUG FIX: use get_or_create instead of direct access — old accounts
            # without wallet rows would crash here and stop all remaining emails
            account_wallet, _ = AccountWallet.objects.get_or_create(user=user)
            yields_wallet, _ = YieldsWallet.objects.get_or_create(user=user)

            send_html_email(
                user=user,
                email_type='WEEKLY_SUMMARY',
                subject='Your Nexcribe Weekly Earnings Summary',
                template_name='weekly_summary.html',
                context={
                    'total_week_usd': f'{total:.2f}',
                    'account_balance': str(account_wallet.balance_usd),
                    'yields_balance': str(yields_wallet.balance_usd),
                    'transaction_count': week_txns.count(),
                },
            )
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f'Weekly summary failed for {user.email}: {e}')

    logger.info(f'Weekly summary complete — sent: {sent}, failed: {failed}')
