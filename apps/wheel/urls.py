from django.urls import path
from .views import WheelConfigView, SpinWheelView, SpinHistoryView

urlpatterns = [
    path('config/', WheelConfigView.as_view(), name='wheel-config'),
    path('spin/', SpinWheelView.as_view(), name='wheel-spin'),
    path('history/', SpinHistoryView.as_view(), name='spin-history'),
]
