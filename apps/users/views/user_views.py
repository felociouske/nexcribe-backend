from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from ..models import Transaction, AccountWallet, YieldsWallet, DepositWallet, CashbackWallet, VirtualCard
from ..serializers import UserSerializer, ProfileSerializer, TransactionSerializer


class VirtualCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualCard
        fields = ['card_number', 'expiry', 'card_name', 'is_active']


class WalletSummarySerializer(serializers.Serializer):
    account_wallet = serializers.SerializerMethodField()
    yields_wallet = serializers.SerializerMethodField()
    deposit_wallet = serializers.SerializerMethodField()
    cashback_wallet = serializers.SerializerMethodField()

    def get_account_wallet(self, user):
        w, _ = AccountWallet.objects.get_or_create(user=user)
        return {
            'balance_usd': str(w.balance_usd),
            'pending_usd': str(w.pending_usd),
            'total_earned_usd': str(w.total_earned_usd),
            'total_withdrawn_usd': str(w.total_withdrawn_usd),
            'balance_kes': str(w.balance_kes),
        }

    def get_yields_wallet(self, user):
        w, _ = YieldsWallet.objects.get_or_create(user=user)
        return {
            'balance_usd': str(w.balance_usd),
            'pending_usd': str(w.pending_usd),
            'total_earned_usd': str(w.total_earned_usd),
            'total_withdrawn_usd': str(w.total_withdrawn_usd),
            'balance_kes': str(w.balance_kes),
        }

    def get_deposit_wallet(self, user):
        w, _ = DepositWallet.objects.get_or_create(user=user)
        return {
            'balance_usd': str(w.balance_usd),
            'total_deposited_usd': str(w.total_deposited_usd),
            'total_spent_usd': str(w.total_spent_usd),
            'balance_kes': str(w.balance_kes),
        }

    def get_cashback_wallet(self, user):
        w, _ = CashbackWallet.objects.get_or_create(user=user)
        return {
            'balance_usd': str(w.balance_usd),
            'total_earned_usd': str(w.total_earned_usd),
            'balance_kes': str(w.balance_kes),
        }


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        profile_data = request.data.get('profile', {})
        if profile_data:
            profile_serializer = ProfileSerializer(instance.profile, data=profile_data, partial=True)
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()
        return Response(serializer.data)


class WalletsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = WalletSummarySerializer(request.user)
        return Response(serializer.data)


class VirtualCardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        card, _ = VirtualCard.objects.get_or_create(user=request.user)
        return Response(VirtualCardSerializer(card).data)


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['wallet_type', 'type', 'source', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class ReferralInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = user.profile
        from django.conf import settings
        referral_link = f"{settings.FRONTEND_URL}/ref/{profile.referral_code}"
        return Response({
            'referral_code': profile.referral_code,
            'referral_link': referral_link,
            'total_referrals': profile.total_referrals,
        })