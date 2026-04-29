from django.urls import path
from .views import (
    RequestDepositView, MyDepositsView,
    AdminDepositListView, AdminProcessDepositView,
    RequestWithdrawalView, MyWithdrawalsView,
    AdminWithdrawalListView, AdminProcessWithdrawalView,
)

urlpatterns = [
    path('deposit/', RequestDepositView.as_view(), name='request-deposit'),
    path('deposits/', MyDepositsView.as_view(), name='my-deposits'),
    path('admin/deposits/', AdminDepositListView.as_view(), name='admin-deposits'),
    path('admin/deposits/<uuid:pk>/process/', AdminProcessDepositView.as_view(), name='admin-process-deposit'),
    path('withdraw/', RequestWithdrawalView.as_view(), name='request-withdrawal'),
    path('withdrawals/', MyWithdrawalsView.as_view(), name='my-withdrawals'),
    path('admin/withdrawals/', AdminWithdrawalListView.as_view(), name='admin-withdrawals'),
    path('admin/withdrawals/<uuid:pk>/process/', AdminProcessWithdrawalView.as_view(), name='admin-process-withdrawal'),
]