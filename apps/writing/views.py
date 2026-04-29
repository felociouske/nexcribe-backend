from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.conf import settings
from django.db.models import Count
from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
import logging
import random
from datetime import timedelta

from .models import WritingJob, Category, WritingJobHistory
from .serializers import WritingJobSerializer, CategorySerializer, WritingJobHistorySerializer
from apps.core.models import generate_transaction_code
from apps.users.models import Transaction, AccountWallet

logger = logging.getLogger(__name__)


def get_user_writing_plan(user):
    return user.user_plans.filter(
        plan__category='WRITING', status='ACTIVE'
    ).select_related('plan').first()


def get_week_start():
    """Return the start of the current ISO week (Monday 00:00 UTC)."""
    today = timezone.now().date()
    return today - timedelta(days=today.weekday())


def get_tasks_used_this_week(user, user_plan):
    """Count how many writing tasks the user submitted this week."""
    week_start = get_week_start()
    return WritingJobHistory.objects.filter(
        user=user,
        action='SUBMITTED',
        created_at__date__gte=week_start,
    ).count()


class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.filter(is_active=True)


class WritingJobListView(generics.ListAPIView):
    serializer_class = WritingJobSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['difficulty', 'status']
    search_fields = ['title', 'description']

    def get_queryset(self):
        user = self.request.user
        user_plan = get_user_writing_plan(user)

        # Issue 6: Show all OPEN jobs even without a plan — user just can't accept them.
        # This mirrors how transcription works.
        all_open = WritingJob.objects.filter(
            status=WritingJob.STATUS_OPEN,
        ).select_related('category')

        if not user_plan:
            # Show all jobs — frontend will show "Purchase a plan" on accept attempt
            eligible = list(all_open)
            random.shuffle(eligible)
            ids = [job.id for job in eligible[:20]]
            return WritingJob.objects.filter(id__in=ids).select_related('category')

        plan = user_plan.plan

        # Issue 3: weekly limit instead of monthly
        limit = plan.writing_tasks_per_month  # field name stays, but we treat it as weekly
        tasks_used_this_week = get_tasks_used_this_week(user, user_plan)
        remaining = (limit - tasks_used_this_week) if limit != 9999 else 9999

        if remaining <= 0:
            return WritingJob.objects.none()

        eligible = list(
            all_open.filter(minimum_plan_level__lte=plan.level)
        )
        random.shuffle(eligible)
        ids = [job.id for job in eligible[:remaining]]
        return WritingJob.objects.filter(id__in=ids).select_related('category')


class MyWritingJobsView(generics.ListAPIView):
    serializer_class = WritingJobSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_queryset(self):
        # Show jobs accepted this week that haven't been submitted yet
        week_start = get_week_start()
        submitted_job_ids = WritingJobHistory.objects.filter(
            user=self.request.user, action='SUBMITTED',
            created_at__date__gte=week_start,
        ).values_list('job_id', flat=True)

        accepted_job_ids = WritingJobHistory.objects.filter(
            user=self.request.user, action='ACCEPTED',
            created_at__date__gte=week_start,
        ).exclude(job_id__in=submitted_job_ids).values_list('job_id', flat=True)

        return WritingJob.objects.filter(id__in=accepted_job_ids).select_related('category')


class WritingJobDetailView(generics.RetrieveAPIView):
    serializer_class = WritingJobSerializer
    permission_classes = [IsAuthenticated]
    queryset = WritingJob.objects.select_related('category', 'assigned_to')


class AcceptJobView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        try:
            job = WritingJob.objects.get(id=pk, status=WritingJob.STATUS_OPEN)
        except WritingJob.DoesNotExist:
            return Response({'error': 'Job not found or no longer available.'}, status=404)

        user_plan = get_user_writing_plan(user)
        if not user_plan:
            return Response({'error': 'You need an active Writing plan to accept jobs.'}, status=403)

        plan = user_plan.plan
        if plan.level < job.minimum_plan_level:
            return Response({'error': f'This job requires Level {job.minimum_plan_level}+.'}, status=403)

        # Issue 3: weekly limit check
        limit = plan.writing_tasks_per_month
        tasks_used_this_week = get_tasks_used_this_week(user, user_plan)
        if limit != 9999 and tasks_used_this_week >= limit:
            return Response({'error': f'Weekly task limit of {limit} reached. Resets next Monday.'}, status=403)

        # Issue 2: allow re-doing — only block if already accepted THIS WEEK and not yet submitted
        week_start = get_week_start()
        already_accepted_this_week = WritingJobHistory.objects.filter(
            job=job, user=user, action='ACCEPTED',
            created_at__date__gte=week_start,
        ).exists()
        already_submitted_this_week = WritingJobHistory.objects.filter(
            job=job, user=user, action='SUBMITTED',
            created_at__date__gte=week_start,
        ).exists()

        if already_accepted_this_week and not already_submitted_this_week:
            return Response({'message': 'Already accepted — check My Jobs.', 'job_id': str(job.id)})

        # Job stays OPEN — multiple users, multiple weeks
        WritingJobHistory.objects.create(job=job, user=user, action='ACCEPTED')

        try:
            from apps.notifications.utils import create_notification
            create_notification(
                user, 'TASK_ASSIGNED',
                f'Job Accepted: {job.title[:40]}',
                f'You accepted "{job.title}". Upload your document when ready.',
                '/dashboard/writing',
            )
        except Exception as e:
            logger.warning(f'Notification failed: {e}')

        return Response({'message': 'Job accepted.', 'job_id': str(job.id)})


class SubmitJobView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, pk):
        user = request.user

        try:
            job = WritingJob.objects.get(id=pk, status=WritingJob.STATUS_OPEN)
        except WritingJob.DoesNotExist:
            return Response({'error': 'Job not found or no longer available.'}, status=404)

        # Must have accepted this job this week
        week_start = get_week_start()
        accepted_this_week = WritingJobHistory.objects.filter(
            job=job, user=user, action='ACCEPTED',
            created_at__date__gte=week_start,
        ).exists()
        if not accepted_this_week:
            return Response({'error': 'You have not accepted this job this week.'}, status=403)

        # Prevent double submission this week
        already_submitted_this_week = WritingJobHistory.objects.filter(
            job=job, user=user, action='SUBMITTED',
            created_at__date__gte=week_start,
        ).exists()
        if already_submitted_this_week:
            return Response({'error': 'Already submitted this job this week.'}, status=400)

        uploaded_file = request.FILES.get('document')
        word_count = request.data.get('word_count', 0)

        if uploaded_file:
            job.submission_file = uploaded_file
            job.submission_filename = uploaded_file.name
        else:
            filename = request.data.get('filename', '').strip()
            if not filename:
                return Response({'error': 'Please upload your document file.'}, status=400)
            job.submission_filename = filename

        job.submission_word_count = int(word_count) if word_count else 0
        job.submitted_at = timezone.now()

        # Pay immediately on submission
        amount_kes = Decimal(str(job.budget_kes))
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
            source='WRITING',
            description=f'Writing job completed: {job.title[:60]}',
            status='COMPLETED',
            balance_after_usd=wallet.balance_usd,
        )

        job.payment_transaction_code = txn_code
        job.payment_amount_usd = amount_usd
        # Job remains OPEN so others (and this user next week) can do it again
        job.save()

        WritingJobHistory.objects.create(
            job=job, user=user, action='SUBMITTED',
            note=job.submission_filename,
            transaction_code=txn_code,
            amount_usd=amount_usd,
        )

        try:
            from apps.notifications.utils import create_notification
            create_notification(
                user, 'TASK_APPROVED',
                f'Writing Job Paid — +${amount_usd}',
                f'"{job.title}" submitted! ${amount_usd} (KES {amount_kes}) credited to your Account Wallet.',
                '/dashboard/wallet',
                metadata={'amount_usd': str(amount_usd), 'txn_code': txn_code},
            )
        except Exception as e:
            logger.warning(f'Notification failed: {e}')

        try:
            from apps.notifications.utils import send_html_email
            send_html_email(
                user=user,
                email_type='WRITING_TASK_PAID',
                subject=f'Payment Received — {job.title[:40]}',
                template_name='task_update.html',
                context={
                    'task_type': 'Writing',
                    'task_title': job.title,
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
        })


class WritingJobHistoryView(generics.ListAPIView):
    serializer_class = WritingJobHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WritingJobHistory.objects.filter(
            user=self.request.user
        ).select_related('job').order_by('-created_at')