from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from decimal import Decimal
import logging

from .models import DepositRequest, WithdrawalRequest, MpesaPaymentDetails
from apps.users.models import Transaction as TxnModel
from apps.core.models import generate_transaction_code
from apps.notifications.utils import create_notification

logger = logging.getLogger(__name__)

class MpesaPaymentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaPaymentDetails
        fields = ['phone_number', 'account_name']


class DepositRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositRequest
        fields = [
            'id', 'transaction_code', 'mpesa_code', 'phone_number',
            'amount_kes', 'amount_usd', 'status', 'admin_note',
            'processed_at', 'created_at',
        ]
        read_only_fields = ['id', 'transaction_code', 'amount_usd', 'status',
                            'admin_note', 'processed_at', 'created_at']


class CreateDepositSerializer(serializers.Serializer):
    mpesa_code = serializers.CharField(max_length=30)
    phone_number = serializers.CharField(max_length=20)
    amount_kes = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('100'))


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'transaction_code', 'wallet_type', 'amount_usd', 'amount_kes',
            'method', 'phone_number', 'account_details', 'status',
            'admin_note', 'mpesa_receipt', 'processed_at', 'created_at',
        ]
        read_only_fields = ['id', 'transaction_code', 'amount_kes', 'status',
                            'admin_note', 'mpesa_receipt', 'processed_at', 'created_at']


class CreateWithdrawalSerializer(serializers.Serializer):
    wallet_type = serializers.ChoiceField(choices=['ACCOUNT', 'YIELDS'])
    amount_usd = serializers.DecimalField(max_digits=10, decimal_places=2)
    method = serializers.ChoiceField(choices=['MPESA', 'CARD'])
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    account_details = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_amount_usd(self, value):
        min_val = Decimal(str(settings.MINIMUM_WITHDRAWAL_USD))
        if value < min_val:
            raise serializers.ValidationError(f'Minimum withdrawal is ${settings.MINIMUM_WITHDRAWAL_USD}.')
        return value

    def validate(self, attrs):
        if attrs['method'] == 'MPESA' and not attrs.get('phone_number'):
            raise serializers.ValidationError({'phone_number': 'Required for M-Pesa.'})
        if attrs['method'] == 'CARD' and not attrs.get('account_details'):
            raise serializers.ValidationError({'account_details': 'Required for card.'})
        return attrs


# ── Deposit Views ──

class RequestDepositView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateDepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        amount_kes = Decimal(str(data['amount_kes']))
        amount_usd = (amount_kes / Decimal(str(settings.KES_TO_USD_RATE))).quantize(Decimal('0.01'))

        deposit = DepositRequest.objects.create(
            user=request.user,
            mpesa_code=data['mpesa_code'].upper(),
            phone_number=data['phone_number'],
            amount_kes=amount_kes,
            amount_usd=amount_usd,
            status=DepositRequest.STATUS_PENDING,
        )

        try:
            create_notification(
                user=request.user,
                notification_type='SYSTEM',
                title='Deposit Submitted',
                message=f'Your deposit of KES {amount_kes} (M-Pesa: {deposit.mpesa_code}) '
                        f'has been submitted and is awaiting admin approval.',
                link='/dashboard/wallet',
                metadata={'txn_code': deposit.transaction_code, 'amount_kes': str(amount_kes)},
            )
        except Exception as e:
            logger.warning(f'Deposit notification failed: {e}')

        return Response({
            'message': 'Deposit submitted. Admin will verify and approve within 24 hours.',
            'transaction_code': deposit.transaction_code,
            'amount_kes': str(amount_kes),
            'amount_usd': str(amount_usd),
            'status': 'PENDING',
        }, status=status.HTTP_201_CREATED)


class MyDepositsView(generics.ListAPIView):
    serializer_class = DepositRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DepositRequest.objects.filter(user=self.request.user)


class AdminDepositListView(generics.ListAPIView):
    serializer_class = DepositRequestSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = DepositRequest.objects.select_related('user').all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs


class AdminProcessDepositView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            deposit = DepositRequest.objects.get(id=pk)
        except DepositRequest.DoesNotExist:
            return Response({'error': 'Deposit not found.'}, status=404)

        if deposit.status != DepositRequest.STATUS_PENDING:
            return Response({'error': f'Deposit already {deposit.status.lower()}.'}, status=400)

        action = request.data.get('action')
        note = request.data.get('note', '')

        if action not in ['approve', 'reject']:
            return Response({'error': 'action must be "approve" or "reject".'}, status=400)

        deposit.admin_note = note
        deposit.processed_by = request.user
        deposit.processed_at = timezone.now()

        if action == 'approve':
            deposit.status = DepositRequest.STATUS_APPROVED
            deposit.save()

            from apps.users.models import DepositWallet
            wallet, _ = DepositWallet.objects.get_or_create(user=deposit.user)
            wallet.balance_usd += deposit.amount_usd
            wallet.total_deposited_usd += deposit.amount_usd
            wallet.save()

            TxnModel.objects.create(
                user=deposit.user,
                transaction_code=generate_transaction_code(),
                wallet_type='DEPOSIT',
                type='CREDIT',
                amount_usd=deposit.amount_usd,
                amount_kes=deposit.amount_kes,
                source='DEPOSIT',
                description=f'M-Pesa deposit approved — {deposit.mpesa_code}',
                status='COMPLETED',
                reference=deposit.mpesa_code,
                balance_after_usd=wallet.balance_usd,
            )

            try:
                create_notification(
                    deposit.user, 'SYSTEM',
                    f'Deposit Approved — KES {deposit.amount_kes}',
                    f'Your deposit of KES {deposit.amount_kes} has been approved '
                    f'and credited to your Deposit Wallet.',
                    '/dashboard/wallet',
                    metadata={
                        'amount_usd': str(deposit.amount_usd),
                        'amount_kes': str(deposit.amount_kes),
                    },
                )
            except Exception as e:
                logger.warning(f'Notification failed: {e}')

        else:
            deposit.status = DepositRequest.STATUS_REJECTED
            deposit.save()
            try:
                create_notification(
                    deposit.user, 'SYSTEM',
                    'Deposit Rejected',
                    f'Your deposit of KES {deposit.amount_kes} '
                    f'(M-Pesa: {deposit.mpesa_code}) was rejected.'
                    + (f' Reason: {note}' if note else ' Please contact support.'),
                    '/dashboard/wallet',
                    metadata={'admin_note': note},
                )
            except Exception as e:
                logger.warning(f'Notification failed: {e}')

        return Response({'message': f'Deposit {action}d.', 'transaction_code': deposit.transaction_code})


# ── Withdrawal Views ──

class RequestWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateWithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        amount_usd = Decimal(str(data['amount_usd']))
        amount_kes = (amount_usd * Decimal(str(settings.KES_TO_USD_RATE))).quantize(Decimal('0.01'))
        wallet_type = data['wallet_type']

        from apps.users.models import AccountWallet, YieldsWallet
        if wallet_type == 'ACCOUNT':
            wallet, _ = AccountWallet.objects.get_or_create(user=user)
        else:
            wallet, _ = YieldsWallet.objects.get_or_create(user=user)

        if wallet.balance_usd < amount_usd:
            return Response({'error': 'Insufficient balance.'}, status=400)

        if WithdrawalRequest.objects.filter(
            user=user, wallet_type=wallet_type, status=WithdrawalRequest.STATUS_PENDING
        ).exists():
            return Response({'error': 'You already have a pending withdrawal.'}, status=400)

        with transaction.atomic():
            wallet = wallet.__class__.objects.select_for_update().get(pk=wallet.pk)
            wallet.balance_usd -= amount_usd
            wallet.pending_usd += amount_usd
            wallet.save()

            withdrawal = WithdrawalRequest.objects.create(
                user=user,
                wallet_type=wallet_type,
                amount_usd=amount_usd,
                amount_kes=amount_kes,
                method=data['method'],
                phone_number=data.get('phone_number', ''),
                account_details=data.get('account_details', ''),
            )

            TxnModel.objects.create(
                user=user,
                transaction_code=withdrawal.transaction_code,
                wallet_type=wallet_type,
                type='DEBIT',
                amount_usd=amount_usd,
                amount_kes=amount_kes,
                source='WITHDRAWAL',
                description=f'Withdrawal request via {data["method"]}',
                status='PENDING',
                balance_after_usd=wallet.balance_usd,
            )

        try:
            create_notification(
                user=user,
                notification_type='WITHDRAWAL',
                title='Withdrawal Requested',
                message=f'Your withdrawal of ${amount_usd} from '
                        f'{"Account" if wallet_type == "ACCOUNT" else "Yields"} Wallet '
                        f'is being processed. Txn: {withdrawal.transaction_code}',
                link='/dashboard/wallet',
                metadata={
                    'txn_code': withdrawal.transaction_code,
                    'amount_usd': str(amount_usd),
                    'status': 'PENDING',
                },
            )
        except Exception as e:
            logger.warning(f'Withdrawal notification failed: {e}')

        try:
            from apps.notifications.utils import send_html_email
            from django.conf import settings
            amount_kes = float(amount_usd) * settings.KES_TO_USD_RATE
            wallet_label = 'Account Wallet' if wallet_type == 'ACCOUNT' else 'Yields Wallet'
            send_html_email(
                user=user,
                email_type='WITHDRAWAL_PENDING',
                subject=f'Withdrawal Pending — {withdrawal.transaction_code}',
                template_name='withdrawal_update.html',
                context={
                    'amount_usd': amount_usd,
                    'amount_kes': f'{amount_kes:.2f}',
                    'wallet_label': wallet_label,
                    'status': 'PENDING',
                    'txn_code': withdrawal.transaction_code,
                    'reason': '',
                },
            )
        except Exception as e:
            logger.warning(f'Withdrawal email failed: {e}')

        return Response({
            'message': 'Withdrawal submitted. Processing within 24 hours.',
            'transaction_code': withdrawal.transaction_code,
            'amount_usd': str(amount_usd),
        }, status=status.HTTP_201_CREATED)


class MyWithdrawalsView(generics.ListAPIView):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(user=self.request.user)


class AdminWithdrawalListView(generics.ListAPIView):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = WithdrawalRequest.objects.select_related('user').all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs


class AdminProcessWithdrawalView(APIView):
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, pk):
        try:
            withdrawal = WithdrawalRequest.objects.select_for_update().get(id=pk)
        except WithdrawalRequest.DoesNotExist:
            return Response({'error': 'Not found.'}, status=404)

        if withdrawal.status != WithdrawalRequest.STATUS_PENDING:
            return Response({'error': 'Already processed.'}, status=400)

        action = request.data.get('action')
        note = request.data.get('note', '')
        receipt = request.data.get('mpesa_receipt', '')

        if action not in ['approve', 'reject']:
            return Response({'error': 'action must be "approve" or "reject".'}, status=400)

        user = withdrawal.user
        wallet_type = withdrawal.wallet_type
        wallet_label = 'Account Wallet' if wallet_type == 'ACCOUNT' else 'Yields Wallet'

        from apps.users.models import AccountWallet, YieldsWallet
        if wallet_type == 'ACCOUNT':
            wallet = AccountWallet.objects.select_for_update().get(user=user)
        else:
            wallet = YieldsWallet.objects.select_for_update().get(user=user)

        if wallet.pending_usd < withdrawal.amount_usd:
            return Response({'error': 'Invalid wallet state.'}, status=400)

        if action == 'approve':
            withdrawal.status = WithdrawalRequest.STATUS_APPROVED
            withdrawal.mpesa_receipt = receipt
            withdrawal.admin_note = note
            withdrawal.processed_by = request.user
            withdrawal.processed_at = timezone.now()

            wallet.pending_usd -= withdrawal.amount_usd
            wallet.total_withdrawn_usd += withdrawal.amount_usd

            TxnModel.objects.filter(
                transaction_code=withdrawal.transaction_code
            ).update(status='COMPLETED')

        else:  # reject
            withdrawal.status = WithdrawalRequest.STATUS_REJECTED
            withdrawal.admin_note = note
            withdrawal.processed_by = request.user
            withdrawal.processed_at = timezone.now()

            # Return amount from pending back to available balance
            wallet.pending_usd -= withdrawal.amount_usd
            wallet.balance_usd += withdrawal.amount_usd

            logger.info(
                f'Withdrawal {withdrawal.transaction_code} REJECTED — '
                f'restoring ${withdrawal.amount_usd} to {wallet_type} wallet '
                f'for user {user.email}. '
                f'New balance_usd={wallet.balance_usd} pending_usd={wallet.pending_usd}'
            )

            TxnModel.objects.filter(
                transaction_code=withdrawal.transaction_code
            ).update(status='REVERSED')

        wallet.save()
        withdrawal.save()

        # On rejection, create a CREDIT transaction so the reversal is visible
        # in the user's transaction history and the balance_after shows correctly.
        if action == 'reject':
            TxnModel.objects.create(
                user=user,
                transaction_code=generate_transaction_code(),
                wallet_type=wallet_type,
                type='CREDIT',
                amount_usd=withdrawal.amount_usd,
                amount_kes=withdrawal.amount_kes,
                source='WITHDRAWAL_REVERSAL',
                description=f'Withdrawal rejected — funds returned to {wallet_label}',
                status='COMPLETED',
                balance_after_usd=wallet.balance_usd,
            )

        # BUG FIX: create notification synchronously here — do NOT rely solely
        # on the Celery task. If Celery is down the user would never see any
        # notification about their withdrawal being rejected or approved.
        try:
            if action == 'approve':
                create_notification(
                    user=user,
                    notification_type='WITHDRAWAL',
                    title=f'Withdrawal Approved — ${withdrawal.amount_usd}',
                    message=(
                        f'Your withdrawal of ${withdrawal.amount_usd} from {wallet_label} '
                        f'has been approved and processed.'
                        + (f' M-Pesa Receipt: {receipt}' if receipt else '')
                        + (f' Note: {note}' if note else '')
                    ),
                    link='/dashboard/wallet',
                    metadata={
                        'txn_code': withdrawal.transaction_code,
                        'amount_usd': str(withdrawal.amount_usd),
                        'status': 'APPROVED',
                        'admin_note': note,
                        'mpesa_receipt': receipt,
                    },
                )
            else:
                create_notification(
                    user=user,
                    notification_type='WITHDRAWAL',
                    title=f'Withdrawal Rejected — ${withdrawal.amount_usd}',
                    message=(
                        f'Your withdrawal of ${withdrawal.amount_usd} from {wallet_label} '
                        f'was rejected. Your balance has been restored.'
                        + (f' Reason: {note}' if note else '')
                    ),
                    link='/dashboard/wallet',
                    metadata={
                        'txn_code': withdrawal.transaction_code,
                        'amount_usd': str(withdrawal.amount_usd),
                        'status': 'REJECTED',
                        'admin_note': note,
                    },
                )
        except Exception as e:
            logger.warning(f'Withdrawal notification failed: {e}')

        # Send email directly (no Celery)
        try:
            from apps.notifications.utils import send_html_email
            from django.conf import settings
            amount_kes = float(withdrawal.amount_usd) * settings.KES_TO_USD_RATE
            wallet_label = 'Account Wallet' if wallet_type == 'ACCOUNT' else 'Yields Wallet'
            send_html_email(
                user=user,
                email_type=f'WITHDRAWAL_{withdrawal.status}',
                subject=f'Withdrawal {withdrawal.status.title()} — {withdrawal.transaction_code}',
                template_name='withdrawal_update.html',
                context={
                    'amount_usd': str(withdrawal.amount_usd),
                    'amount_kes': f'{amount_kes:.2f}',
                    'wallet_label': wallet_label,
                    'status': withdrawal.status,
                    'txn_code': withdrawal.transaction_code,
                    'reason': note,
                },
            )
        except Exception as e:
            logger.warning(f'Withdrawal email task failed (non-critical): {e}')

        return Response({
            'message': f'Withdrawal {action}d.',
            'status': withdrawal.status,
        })


class MpesaPaymentDetailsView(generics.RetrieveAPIView):
    serializer_class = MpesaPaymentDetailsSerializer
    permission_classes = []

    def get_object(self):
        # Return the active M-Pesa payment details
        return MpesaPaymentDetails.objects.filter(is_active=True).first()