from django.urls import path
from .views import NotificationListView, MarkReadView, UnreadCountView, AdminSendRemarkView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications'),
    path('unread-count/', UnreadCountView.as_view(), name='unread-count'),
    path('mark-read/', MarkReadView.as_view(), name='mark-all-read'),
    path('<uuid:pk>/read/', MarkReadView.as_view(), name='mark-read'),
    path('admin/send-remark/', AdminSendRemarkView.as_view(), name='admin-send-remark'),
]