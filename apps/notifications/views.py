from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'is_read',
            'link', 'metadata', 'admin_remark', 'created_at',
        ]


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        unread_only = self.request.query_params.get('unread')
        if unread_only:
            qs = qs.filter(is_read=False)
        return qs


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        if pk:
            Notification.objects.filter(id=pk, user=request.user).update(is_read=True)
        else:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'Marked as read.'})


class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


class AdminSendRemarkView(APIView):
    """Admin sends a personal remark/notification to a specific user."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        from apps.users.models import User
        user_id = request.data.get('user_id')
        user_email = request.data.get('user_email')
        title = request.data.get('title', '').strip()
        message = request.data.get('message', '').strip()
        link = request.data.get('link', '')
        remark = request.data.get('remark', '')

        if not title or not message:
            return Response({'error': 'title and message are required.'}, status=400)

        try:
            if user_id:
                user = User.objects.get(id=user_id)
            elif user_email:
                user = User.objects.get(email=user_email)
            else:
                return Response({'error': 'user_id or user_email required.'}, status=400)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        notification = Notification.objects.create(
            user=user,
            type='ADMIN_REMARK',
            title=title,
            message=message,
            link=link,
            admin_remark=remark,
            sent_by_admin=request.user,
        )

        return Response({
            'message': f'Remark sent to {user.email}.',
            'notification_id': str(notification.id),
        })