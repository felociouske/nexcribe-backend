from rest_framework import generics, serializers, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
import logging

from .models import TranscriptionTask, TranscriptionSubmission
from apps.core.models import generate_transaction_code
from apps.users.models import Transaction, AccountWallet

logger = logging.getLogger(__name__)


class TranscriptionTaskSerializer(serializers.ModelSerializer):
    pay_usd = serializers.ReadOnlyField()
    duration_minutes = serializers.ReadOnlyField()
    is_claimed_by_me = serializers.SerializerMethodField()
    audio_file_url = serializers.SerializerMethodField()

    class Meta:
        model = TranscriptionTask
        fields = [
            'id', 'title', 'description', 'source', 'difficulty', 'language',
            'duration_seconds', 'duration_minutes', 'pay_kes', 'pay_usd',
            'minimum_plan_level', 'status', 'audio_url', 'audio_file_url',
            'book_title', 'book_author', 'is_claimed_by_me', 'claim_expires_at', 'created_at',
        ]

    def get_is_claimed_by_me(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.assigned_to_id == request.user.id
        return False

    def get_audio_file_url(self, obj):
        """Return URL for admin-uploaded audio files stored in the backend."""
        request = self.context.get('request')
        if obj.audio_file and request:
            return request.build_absolute_uri(obj.audio_file.url)
        return None


class TranscriptionSubmissionSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_pay_usd = serializers.SerializerMethodField()
    task_audio_url = serializers.CharField(source='task.audio_url', read_only=True)

    class Meta:
        model = TranscriptionSubmission
        fields = [
            'id', 'task', 'task_title', 'task_pay_usd', 'task_audio_url',
            'word_count', 'status', 'admin_feedback',
            'transaction_code', 'reviewed_at', 'created_at',
        ]

    def get_task_pay_usd(self, obj):
        return obj.task.pay_usd


def get_user_transcription_plan(user):
    return user.user_plans.filter(
        plan__category='TRANSCRIPTION', status='ACTIVE'
    ).select_related('plan').first()


class TranscriptionTaskListView(generics.ListAPIView):
    serializer_class = TranscriptionTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['difficulty', 'language', 'source']
    search_fields = ['title', 'book_title', 'book_author']
    ordering_fields = ['pay_kes', 'duration_seconds', 'created_at']

    def get_queryset(self):
        user = self.request.user
        user_plan = get_user_transcription_plan(user)

        base_qs = TranscriptionTask.objects.filter(status=TranscriptionTask.STATUS_AVAILABLE)

        if not user_plan:
            # No plan — show all available tasks so user can browse
            # Frontend will block claiming until they purchase
            return base_qs.order_by('?')[:30]

        plan = user_plan.plan

        # Difficulty access map — default to showing ALL if unknown value
        difficulty_map = {
            'BASIC':  ['BASIC'],
            'EASY':   ['BASIC', 'EASY'],
            'MEDIUM': ['BASIC', 'EASY', 'MEDIUM'],
            'HARD':   ['BASIC', 'EASY', 'MEDIUM', 'HARD'],
            'ALL':    ['BASIC', 'EASY', 'MEDIUM', 'HARD'],
        }
        diff_access = getattr(plan, 'transcription_difficulty_access', 'ALL') or 'ALL'
        allowed = difficulty_map.get(diff_access.upper(), ['BASIC', 'EASY', 'MEDIUM', 'HARD'])

        # Level 1 (Scribe) sees ALL minimum_plan_level=1 tasks in their difficulty range
        # No audio duration filter — all tasks are accessible
        return base_qs.filter(
            minimum_plan_level__lte=plan.level,
            difficulty__in=allowed,
        )


class MyTranscriptionTasksView(generics.ListAPIView):
    serializer_class = TranscriptionTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TranscriptionTask.objects.filter(assigned_to=self.request.user)


class TranscriptionTaskDetailView(generics.RetrieveAPIView):
    serializer_class = TranscriptionTaskSerializer
    permission_classes = [IsAuthenticated]
    queryset = TranscriptionTask.objects.all()


class ClaimTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        user_plan = get_user_transcription_plan(user)

        if not user_plan:
            return Response(
                {'error': 'You need an active Transcription plan to claim tasks.'},
                status=403
            )

        # Weekly limit check
        from datetime import timedelta
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())

        limit = user_plan.plan.transcription_tasks_per_month  # treated as weekly
        tasks_this_week = TranscriptionSubmission.objects.filter(
            user=user,
            created_at__date__gte=week_start,
        ).count()

        if limit != 9999 and tasks_this_week >= limit:
            return Response({'error': f'Weekly task limit of {limit} reached. Resets next Monday.'}, status=403)

        try:
            task = TranscriptionTask.objects.get(id=pk)
        except TranscriptionTask.DoesNotExist:
            return Response({'error': 'Task not found.'}, status=404)

        if task.assigned_to_id == user.id and task.status == TranscriptionTask.STATUS_ASSIGNED:
            return Response({
                'message': 'Task already claimed by you.',
                'task_id': str(task.id),
                'expires_at': task.claim_expires_at.isoformat() if task.claim_expires_at else None,
                'audio_url': task.audio_url,
            })

        if task.status != TranscriptionTask.STATUS_AVAILABLE:
            return Response({'error': 'Task not available.'}, status=409)

        if task.assigned_to and task.is_claim_expired():
            task.assigned_to = None
            task.assigned_at = None
            task.claim_expires_at = None
            task.status = TranscriptionTask.STATUS_AVAILABLE

        if task.assigned_to:
            return Response({'error': 'Task already claimed by another user.'}, status=409)

        task.status = TranscriptionTask.STATUS_ASSIGNED
        task.assigned_to = user
        task.assigned_at = timezone.now()
        task.claim_expires_at = timezone.now() + timedelta(hours=24)
        task.save()

        user_plan.transcription_tasks_used += 1
        user_plan.save()

        return Response({
            'message': 'Task claimed! You have 24 hours to submit.',
            'task_id': str(task.id),
            'expires_at': task.claim_expires_at.isoformat(),
            'audio_url': task.audio_url,
        })


class SubmitTranscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        try:
            task = TranscriptionTask.objects.get(
                id=pk, assigned_to=user, status=TranscriptionTask.STATUS_ASSIGNED
            )
        except TranscriptionTask.DoesNotExist:
            return Response({'error': 'Task not found or not assigned to you.'}, status=404)

        if task.is_claim_expired():
            task.status = TranscriptionTask.STATUS_AVAILABLE
            task.assigned_to = None
            task.save()
            return Response({'error': 'Your claim expired. Task returned to pool.'}, status=400)

        transcript_text = request.data.get('transcript_text', '').strip()
        if not transcript_text or len(transcript_text) < 50:
            return Response({'error': 'Transcript must be at least 50 characters.'}, status=400)

        if TranscriptionSubmission.objects.filter(task=task, user=user).exists():
            return Response({'error': 'You already submitted this task.'}, status=400)

        # ── Pay immediately on submission — no admin approval needed ──
        amount_kes = Decimal(str(task.pay_kes))
        amount_usd = (
            amount_kes / Decimal(str(settings.KES_TO_USD_RATE))
        ).quantize(Decimal('0.01'))
        txn_code = generate_transaction_code()

        wallet, _ = AccountWallet.objects.get_or_create(user=user)
        wallet.balance_usd      += amount_usd
        wallet.total_earned_usd += amount_usd
        wallet.save()

        Transaction.objects.create(
            user=user,
            transaction_code=txn_code,
            wallet_type='ACCOUNT',
            type='CREDIT',
            amount_usd=amount_usd,
            amount_kes=amount_kes,
            source='TRANSCRIPTION',
            description=f'Transcription completed: {task.title[:60]}',
            status='COMPLETED',
            balance_after_usd=wallet.balance_usd,
        )

        sub = TranscriptionSubmission.objects.create(
            task=task,
            user=user,
            transcript_text=transcript_text,
            word_count=len(transcript_text.split()),
            status=TranscriptionSubmission.STATUS_APPROVED,  # auto-approved
            transaction_code=txn_code,
            reviewed_at=timezone.now(),
        )

        # Task goes back to AVAILABLE so others can do it too
        task.status = TranscriptionTask.STATUS_AVAILABLE
        task.assigned_to = None
        task.assigned_at = None
        task.claim_expires_at = None
        task.save()

        try:
            from apps.notifications.utils import create_notification
            create_notification(
                user, 'TASK_APPROVED',
                f'Transcription Paid — +${amount_usd}',
                f'Your transcription of "{task.title[:50]}" earned ${amount_usd} (KES {amount_kes}). Txn: {txn_code}',
                '/dashboard/wallet',
                metadata={'amount_usd': str(amount_usd), 'txn_code': txn_code},
            )
        except Exception as e:
            logger.warning(f'Notification failed: {e}')

        # Send email directly — no Celery
        try:
            from apps.notifications.utils import send_html_email
            send_html_email(
                user=user,
                email_type='TRANSCRIPTION_TASK_PAID',
                subject=f'Payment Received — {task.title[:40]}',
                template_name='task_update.html',
                context={
                    'task_type': 'Transcription',
                    'task_title': task.title,
                    'status': 'APPROVED',
                    'feedback': '',
                    'amount_usd': str(amount_usd),
                },
            )
        except Exception as e:
            logger.warning(f'Email failed: {e}')

        return Response({
            'message': f'Submitted! ${amount_usd} credited to your Account Wallet.',
            'amount_usd': str(amount_usd),
            'txn_code': txn_code,
            'balance_usd': str(wallet.balance_usd),
        }, status=status.HTTP_201_CREATED)


class MySubmissionsView(generics.ListAPIView):
    serializer_class = TranscriptionSubmissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_queryset(self):
        return TranscriptionSubmission.objects.filter(
            user=self.request.user
        ).select_related('task')


class AudioProxyView(APIView):
    """
    Proxies LibriVox audio through Django so the browser can play it
    inline without CORS errors.

    Browser <audio> tags cannot set Authorization headers, so we accept
    the JWT token as a ?token= query parameter as a fallback.

    GET /api/v1/transcription/tasks/<pk>/audio/
    GET /api/v1/transcription/tasks/<pk>/audio/?token=<jwt>
    """
    permission_classes = [IsAuthenticated]

    def get_authenticators(self):
        """Allow token via query param for browser audio elements."""
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework.authentication import SessionAuthentication

        class QueryParamJWT(JWTAuthentication):
            def authenticate(self, request):
                # Try standard header first
                result = super().authenticate(request)
                if result:
                    return result
                # Fall back to ?token= query param
                token = request.GET.get('token')
                if token:
                    try:
                        validated = self.get_validated_token(token)
                        user = self.get_user(validated)
                        return (user, validated)
                    except Exception:
                        pass
                return None

        return [QueryParamJWT(), SessionAuthentication()]

    def get(self, request, pk):
        import urllib.request
        import urllib.error

        try:
            task = TranscriptionTask.objects.get(id=pk)
        except TranscriptionTask.DoesNotExist:
            return Response({'error': 'Task not found.'}, status=404)

        # If backend has an uploaded audio file, serve that directly
        if task.audio_file:
            from django.http import FileResponse
            return FileResponse(task.audio_file.open('rb'), content_type='audio/mpeg')

        audio_url = task.audio_url
        if not audio_url:
            return Response({'error': 'No audio available for this task.'}, status=404)

        try:
            req = urllib.request.Request(
                audio_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; Nexcribe/1.0)',
                    'Range': request.headers.get('Range', ''),
                }
            )
            remote = urllib.request.urlopen(req, timeout=15)

            from django.http import StreamingHttpResponse

            content_type = remote.headers.get('Content-Type', 'audio/mpeg')
            content_length = remote.headers.get('Content-Length')

            def stream():
                try:
                    while True:
                        chunk = remote.read(32768)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    remote.close()

            response = StreamingHttpResponse(stream(), content_type=content_type)
            response['Accept-Ranges'] = 'bytes'
            response['Access-Control-Allow-Origin'] = '*'
            if content_length:
                response['Content-Length'] = content_length

            return response

        except urllib.error.HTTPError as e:
            logger.error(f'Audio proxy HTTP error for task {pk}: {e.code} {e.reason}')
            return Response({'error': f'Audio source returned {e.code}.'}, status=502)
        except urllib.error.URLError as e:
            logger.error(f'Audio proxy URL error for task {pk}: {e.reason}')
            return Response({'error': 'Could not reach audio source.'}, status=502)
        except Exception as e:
            logger.error(f'Audio proxy error for task {pk}: {e}')
            return Response({'error': 'Audio proxy failed.'}, status=500)