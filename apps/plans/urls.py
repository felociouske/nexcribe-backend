from django.urls import path
from .views import PlanListView, PlanDetailView, MyPlansView, PurchasePlanView, CategorySummaryView

urlpatterns = [
    path('', PlanListView.as_view(), name='plan-list'),
    path('categories/', CategorySummaryView.as_view(), name='plan-categories'),
    path('mine/', MyPlansView.as_view(), name='my-plans'),
    path('<uuid:plan_id>/', PlanDetailView.as_view(), name='plan-detail'),
    path('<uuid:plan_id>/purchase/', PurchasePlanView.as_view(), name='plan-purchase'),
]
