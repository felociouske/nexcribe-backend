from django.urls import path
from .views import (
    TranscriptionTaskListView, TranscriptionTaskDetailView,
    MyTranscriptionTasksView, ClaimTaskView, SubmitTranscriptionView,
    MySubmissionsView, AudioProxyView,
)

urlpatterns = [
    path('tasks/', TranscriptionTaskListView.as_view(), name='transcription-tasks'),
    path('tasks/mine/', MyTranscriptionTasksView.as_view(), name='my-transcription-tasks'),
    path('tasks/<uuid:pk>/', TranscriptionTaskDetailView.as_view(), name='transcription-task-detail'),
    path('tasks/<uuid:pk>/claim/', ClaimTaskView.as_view(), name='transcription-claim'),
    path('tasks/<uuid:pk>/submit/', SubmitTranscriptionView.as_view(), name='transcription-submit'),
    path('tasks/<uuid:pk>/audio/', AudioProxyView.as_view(), name='transcription-audio-proxy'),
    path('submissions/', MySubmissionsView.as_view(), name='transcription-submissions'),
]