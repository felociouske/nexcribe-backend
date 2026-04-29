from django.urls import path
from .views import (
    MyAffiliateNodeView, AffiliateTreeView, DownlineMembersView,
    CommissionListView, EarningsSummaryView,
)

urlpatterns = [
    path('node/', MyAffiliateNodeView.as_view(), name='affiliate-node'),
    path('tree/', AffiliateTreeView.as_view(), name='affiliate-tree'),
    path('downline/<int:level>/', DownlineMembersView.as_view(), name='downline-members'),
    path('commissions/', CommissionListView.as_view(), name='commissions'),
    path('earnings/', EarningsSummaryView.as_view(), name='affiliate-earnings'),
]