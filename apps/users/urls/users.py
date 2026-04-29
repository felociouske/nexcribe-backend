from django.urls import path
from apps.users.views.user_views import (
    MeView, WalletsView, VirtualCardView,
    TransactionListView, ReferralInfoView,
)

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
    path('wallets/', WalletsView.as_view(), name='wallets'),
    path('virtual-card/', VirtualCardView.as_view(), name='virtual-card'),
    path('transactions/', TransactionListView.as_view(), name='transactions'),
    path('referral/', ReferralInfoView.as_view(), name='referral-info'),
]