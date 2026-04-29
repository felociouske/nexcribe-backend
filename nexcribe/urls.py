from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView as SpectacularSwaggerUIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.users.urls.auth')),
    path('api/v1/users/', include('apps.users.urls.users')),
    path('api/v1/plans/', include('apps.plans.urls')),
    path('api/v1/affiliates/', include('apps.affiliates.urls')),
    path('api/v1/writing/', include('apps.writing.urls')),
    path('api/v1/games/', include('apps.games.urls')),
    path('api/v1/wheel/', include('apps.wheel.urls')),
    path('api/v1/transcription/', include('apps.transcription.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    # API Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerUIView.as_view(url_name='schema'), name='swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin branding
admin.site.site_header = 'Nexcribe Admin'
admin.site.site_title = 'Nexcribe'
admin.site.index_title = 'Platform Management'
