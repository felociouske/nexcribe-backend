import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexcribe.settings.production')

app = Celery('nexcribe')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'weekly-earnings-summary': {
        'task': 'apps.notifications.tasks.send_weekly_summary',
        'schedule': crontab(day_of_week='monday', hour=8, minute=0),
    },
    'reset-daily-game-limits': {
        'task': 'apps.games.tasks.reset_daily_limits',
        'schedule': crontab(hour=0, minute=0),
    },
    'reset-daily-wheel-spins': {
        'task': 'apps.wheel.tasks.reset_daily_spins',
        'schedule': crontab(hour=0, minute=0),
    },
}