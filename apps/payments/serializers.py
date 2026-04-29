from rest_framework import serializers
from django.conf import settings
from decimal import Decimal
from .models import WithdrawalRequest


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'transaction_code', 'wallet_type', 'amount_usd', 'amount_kes',
            'method', 'phone_number', 'account_details', 'status',
            'admin_note', 'mpesa_receipt', 'processed_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'transaction_code', 'amount_kes', 'status',
            'admin_note', 'mpesa_receipt', 'processed_at', 'created_at',
        ]


class CreateWithdrawalSerializer(serializers.Serializer):
    wallet_type = serializers.ChoiceField(choices=['ACCOUNT', 'YIELDS'])
    amount_usd = serializers.DecimalField(max_digits=10, decimal_places=2)
    method = serializers.ChoiceField(choices=['MPESA', 'CARD'])
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    account_details = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate_amount_usd(self, value):
        min_withdrawal = Decimal(str(settings.MINIMUM_WITHDRAWAL_USD))
        if value < min_withdrawal:
            raise serializers.ValidationError(
                f'Minimum withdrawal is ${settings.MINIMUM_WITHDRAWAL_USD}.'
            )
        return value

    def validate(self, attrs):
        if attrs['method'] == 'MPESA' and not attrs.get('phone_number'):
            raise serializers.ValidationError({'phone_number': 'Phone number required for M-Pesa.'})
        if attrs['method'] == 'CARD' and not attrs.get('account_details'):
            raise serializers.ValidationError({'account_details': 'Account details required for card withdrawal.'})
        return attrs
