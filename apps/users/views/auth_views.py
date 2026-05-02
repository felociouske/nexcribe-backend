from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
import logging

from apps.users.models import User, EmailVerificationToken, PasswordResetToken
from apps.users.serializers import (
    RegisterSerializer, ChangePasswordSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
)

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        expires = timezone.now() + timedelta(hours=24)
        token = EmailVerificationToken.objects.create(user=user, expires_at=expires)

        try:
            from apps.notifications.tasks import send_welcome_email, send_verification_email
            send_welcome_email.delay(str(user.id))
            send_verification_email.delay(str(user.id), str(token.token))
        except Exception as e:
            logger.warning(f'Email task queuing failed, attempting synchronous send: {e}')
            # Fallback: send synchronously if Celery/broker is unavailable
            try:
                from apps.notifications.utils import send_html_email
                from django.conf import settings
                send_html_email(
                    user=user,
                    email_type='WELCOME',
                    subject='Welcome to Nexcribe — Start Earning Today',
                    template_name='welcome.html',
                    context={'username': user.first_name or user.username},
                )
                verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
                send_html_email(
                    user=user,
                    email_type='EMAIL_VERIFICATION',
                    subject='Verify Your Nexcribe Email Address',
                    template_name='verify_email.html',
                    context={'verify_url': verify_url},
                )
            except Exception as e2:
                logger.error(f'Synchronous email fallback also failed for {user.email}: {e2}')

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Account created. Please verify your email.',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
            }
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token_value = request.data.get('token')
        try:
            token = EmailVerificationToken.objects.get(token=token_value)
            if not token.is_valid():
                return Response({'error': 'Token expired or already used.'}, status=400)
            token.user.is_verified = True
            token.user.save()
            token.is_used = True
            token.save()
            return Response({'message': 'Email verified successfully.'})
        except EmailVerificationToken.DoesNotExist:
            return Response({'error': 'Invalid token.'}, status=400)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
            expires = timezone.now() + timedelta(hours=2)
            token = PasswordResetToken.objects.create(user=user, expires_at=expires)
            try:
                from apps.notifications.tasks import send_password_reset_email
                send_password_reset_email.delay(str(user.id), str(token.token))
            except Exception as e:
                logger.warning(f'Password reset email queuing failed, attempting synchronous send: {e}')
                # Fallback: send synchronously if Celery/broker is unavailable
                try:
                    from apps.notifications.utils import send_html_email
                    from django.conf import settings
                    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
                    send_html_email(
                        user=user,
                        email_type='PASSWORD_RESET',
                        subject='Reset Your Nexcribe Password',
                        template_name='password_reset.html',
                        context={'reset_url': reset_url},
                    )
                except Exception as e2:
                    logger.error(f'Synchronous password reset email fallback also failed for {user.email}: {e2}')
        except User.DoesNotExist:
            pass
        return Response({'message': 'If that email exists, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = PasswordResetToken.objects.get(token=serializer.validated_data['token'])
            if not token.is_valid():
                return Response({'error': 'Token expired or already used.'}, status=400)
            token.user.set_password(serializer.validated_data['new_password'])
            token.user.save()
            token.is_used = True
            token.save()
            return Response({'message': 'Password reset successfully.'})
        except PasswordResetToken.DoesNotExist:
            return Response({'error': 'Invalid token.'}, status=400)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'message': 'Logged out.'})
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            logger.warning(f'Logout error (non-critical): {e}')
        return Response({'message': 'Logged out successfully.'})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Old password is incorrect.'}, status=400)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully.'})