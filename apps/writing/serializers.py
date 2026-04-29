from rest_framework import serializers
from .models import WritingJob, Category, WritingJobHistory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon']


class WritingJobSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    budget_usd = serializers.ReadOnlyField()
    assigned_to_username = serializers.CharField(
        source='assigned_to.username', read_only=True
    )
    is_mine = serializers.SerializerMethodField()
    submission_file_url = serializers.SerializerMethodField()

    class Meta:
        model = WritingJob
        fields = [
            'id', 'title', 'description', 'category', 'category_name',
            'budget_kes', 'budget_usd', 'word_count_required', 'difficulty',
            'minimum_plan_level', 'deadline', 'status', 'instructions',
            'assigned_to_username', 'is_mine',
            'submission_file_url', 'submission_filename', 'submission_word_count',
            'submitted_at', 'completed_at', 'admin_feedback',
            'payment_transaction_code', 'payment_amount_usd',
            'created_at',
        ]

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Jobs stay OPEN — check history for acceptance instead of assigned_to
            return WritingJobHistory.objects.filter(
                job=obj, user=request.user, action='ACCEPTED'
            ).exists()
        return False

    def get_submission_file_url(self, obj):
        if obj.submission_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.submission_file.url)
            return obj.submission_file.url
        return None


class WritingJobHistorySerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = WritingJobHistory
        fields = [
            'id', 'job_title', 'action', 'note',
            'transaction_code', 'amount_usd', 'created_at',
        ]