from django.urls import path
from .views import (
    CategoryListView, WritingJobListView, MyWritingJobsView,
    WritingJobDetailView, AcceptJobView, SubmitJobView,
    WritingJobHistoryView,
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='writing-categories'),
    path('jobs/', WritingJobListView.as_view(), name='writing-jobs'),
    path('jobs/mine/', MyWritingJobsView.as_view(), name='my-writing-jobs'),
    path('jobs/history/', WritingJobHistoryView.as_view(), name='writing-history'),
    path('jobs/<uuid:pk>/', WritingJobDetailView.as_view(), name='writing-job-detail'),
    path('jobs/<uuid:pk>/accept/', AcceptJobView.as_view(), name='writing-accept'),
    path('jobs/<uuid:pk>/submit/', SubmitJobView.as_view(), name='writing-submit'),
    # AdminApproveJobView removed — payment is instant on submission, no admin review needed
]