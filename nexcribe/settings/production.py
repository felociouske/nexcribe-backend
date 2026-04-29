from .base import *

DEBUG = False

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Use real SMTP in production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

CORS_ALLOWED_ORIGINS = [origin.strip() for origin in get_list("CORS_ALLOWED_ORIGINS") if origin]
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False") == "True"
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = get_list(
    "CSRF_TRUSTED_ORIGINS",
    default="https://nexcribe-frontend.vercel.app"
)