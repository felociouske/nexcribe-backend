from django.contrib import admin
from .models import WritingJob, Category, WritingJobHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(WritingJob)
class WritingJobAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'budget_kes', 'difficulty',
        'minimum_plan_level', 'status', 'assigned_to', 'deadline', 'created_at'
    ]
    list_filter = ['status', 'difficulty', 'minimum_plan_level', 'category']
    search_fields = ['title', 'assigned_to__email']
    ordering = ['-created_at']
    readonly_fields = ['submitted_at', 'completed_at']

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WritingJobHistory)
class WritingJobHistoryAdmin(admin.ModelAdmin):
    list_display = ['job', 'user', 'action', 'transaction_code', 'created_at']
    list_filter = ['action']
    readonly_fields = ['job', 'user', 'action', 'note', 'transaction_code', 'created_at']
