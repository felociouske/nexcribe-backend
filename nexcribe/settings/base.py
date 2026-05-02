import os
from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url

def get_list(env_var, default=""):
    return [s.strip() for s in os.getenv(env_var, default).split(",") if s.strip()]

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='nexcribe-dev-secret-change-in-production-xyz123')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

DJANGO_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_celery_beat',
    'django_filters',
    'drf_spectacular',
    'anymail',   
]

LOCAL_APPS = [
    'apps.core',
    'apps.users',
    'apps.plans',
    'apps.affiliates',
    'apps.writing',
    'apps.games',
    'apps.wheel',
    'apps.transcription',
    'apps.notifications',
    'apps.payments',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nexcribe.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nexcribe.wsgi.application'

DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default="sqlite:///db.sqlite3"),
        conn_max_age=600,
        ssl_require=not DEBUG
    )
}

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── REST Framework ──
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ── JWT ──
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ── CORS ──
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_CREDENTIALS = True

# ── Celery ──
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'

# ── Email ──
ANYMAIL = {
    "BREVO_API_KEY": config("BREVO_API_KEY", default=""),
}

EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="Nexcribe <noreply@nexcribe.com>",
)

EMAIL_TIMEOUT = 10

# ── App-specific ──
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')
KES_TO_USD_RATE = 120  # 1 USD = 120 KES
MINIMUM_WITHDRAWAL_USD = 2.00

# ── DRF Spectacular ──
SPECTACULAR_SETTINGS = {
    'TITLE': 'Nexcribe API',
    'DESCRIPTION': 'API for the Nexcribe earning platform',
    'VERSION': '1.0.0',
}



JAZZMIN_SETTINGS = {
    # ── Branding ──
    "site_title": "Nexcribe Admin",
    "site_header": "Nexcribe",
    "site_brand": "Nexcribe",
    "site_logo": None,              # add "images/logo.png" once you have one in /static/
    "login_logo": None,
    "site_icon": None,
    "welcome_sign": "Welcome to Nexcribe Admin Panel",
    "copyright": "Nexcribe Ltd",
 
    # ── Search ──
    "search_model": ["users.User"],
 
    # ── Top navigation quick links ──
    "topmenu_links": [
        {"name": "Dashboard",  "url": "admin:index",            "permissions": ["auth.view_user"]},
        {"name": "Users",      "url": "admin:users_user_changelist"},
        {"name": "Deposits",   "url": "admin:payments_depositrequest_changelist"},
        {"name": "Withdrawals","url": "admin:payments_withdrawalrequest_changelist"},
        {"name": "Notify User","url": "admin:notifications_notification_changelist"},
        {"name": "View Site",  "url": "/api/v1/", "new_window": True},
    ],
 
    # ── User avatar menu (top right) ──
    "usermenu_links": [
        {"name": "View Site", "url": "/api/v1/", "new_window": True},
        {"model": "users.user"},
    ],
 
    # ── Sidebar ──
    "show_sidebar": True,
    "navigation_expanded": True,
 
    # ── Sidebar app/model grouping & ordering ──
    "order_with_respect_to": [
        "users",
        "payments",
        "plans",
        "affiliates",
        "writing",
        "transcription",
        "games",
        "wheel",
        "notifications",
        "django_celery_beat",
        "auth",
    ],
 
    # Custom sidebar icons (Font Awesome 5 free)
    "icons": {
        # Users
        "users.user":                        "fas fa-users",
        "users.profile":                     "fas fa-id-card",
        "users.accountwallet":               "fas fa-wallet",
        "users.yieldswallet":                "fas fa-chart-line",
        "users.depositwallet":               "fas fa-piggy-bank",
        "users.cashbackwallet":              "fas fa-gift",
        "users.transaction":                 "fas fa-exchange-alt",
        "users.virtualcard":                 "fas fa-credit-card",
 
        # Payments
        "payments.depositrequest":           "fas fa-money-bill-wave",
        "payments.withdrawalrequest":        "fas fa-hand-holding-usd",
 
        # Plans
        "plans.plan":                        "fas fa-layer-group",
        "plans.userplan":                    "fas fa-check-circle",
 
        # Affiliates
        "affiliates.affiliatenode":          "fas fa-sitemap",
        "affiliates.commission":             "fas fa-percentage",
 
        # Writing
        "writing.writingjob":                "fas fa-pen-nib",
        "writing.category":                  "fas fa-tags",
        "writing.writingjobhistory":         "fas fa-history",
 
        # Transcription
        "transcription.transcriptiontask":   "fas fa-microphone",
        "transcription.transcriptionsubmission": "fas fa-file-audio",
 
        # Games
        "games.game":                        "fas fa-gamepad",
        "games.gamesession":                 "fas fa-play-circle",
        "games.quizquestion":                "fas fa-question-circle",
        "games.gameleaderboard":             "fas fa-trophy",
 
        # Wheel
        "wheel.wheelconfig":                 "fas fa-dharmachakra",
        "wheel.wheelslice":                  "fas fa-pizza-slice",
        "wheel.spinresult":                  "fas fa-star",
 
        # Notifications
        "notifications.notification":        "fas fa-bell",
        "notifications.emaillog":            "fas fa-envelope",
 
        # Celery beat
        "django_celery_beat.periodictask":   "fas fa-clock",
        "django_celery_beat.crontabschedule":"fas fa-calendar-alt",
 
        # Auth
        "auth.group":                        "fas fa-users-cog",
    },
 
    # Default icon for models not listed above
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
 
    # ── Related modal (open related records in popup, not new tab) ──
    "related_modal_active": True,
 
    # ── UI tweaks ──
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,          # set to True temporarily if you want to
                                       # tweak the theme visually then copy settings
 
    # ── Change list / form layout ──
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "users.user":    "collapsible",
        "plans.plan":    "horizontal_tabs",
        "writing.writingjob": "horizontal_tabs",
    },
 
    # ── Language chooser ──
    "language_chooser": False,
}
 
JAZZMIN_UI_TWEAKS = {
    # ── Theme ──
    # Uses the teal/navy palette matching the Nexcribe frontend.
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
 
    # Sidebar dark navy matches frontend
    "brand_colour":         "navbar-dark",
    "accent":               "accent-teal",
    "navbar":               "navbar-dark",
    "no_navbar_border":     True,
    "navbar_fixed":         True,
    "layout_boxed":         False,
    "footer_fixed":         False,
    "sidebar_fixed":        True,
    "sidebar":              "sidebar-dark-teal",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
 
    # AdminLTE theme — "darkly" gives a sharp dark look,
    # "flatly" gives a clean light look similar to the frontend cards.
    # Options: default, cerulean, cosmo, cyborg, darkly, flatly, journal,
    #          litera, lumen, lux, materia, minty, pulse, sandstone, simplex,
    #          sketchy, slate, solar, spacelab, superhero, united, yeti
    "theme":                "flatly",
    "default_mode_theme":      "auto",
 
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
 
    "actions_sticky_top": True,
}