from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_html_email(user, email_type, subject, template_name, context):
    """
    Render an HTML email template and send it.
    Logs outcome to EmailLog.
    """
    from apps.notifications.models import EmailLog

    context.update({
        'user': user,
        'site_name': 'Nexcribe',
        'site_url': settings.FRONTEND_URL,
        'support_email': 'support@nexcribe.com',
    })

    try:
        html_content = render_to_string(f'emails/{template_name}', context)
        text_content = context.get('plain_text', f'Hello {user.first_name or user.username},\n\n{subject}')

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()

        EmailLog.objects.create(
            user=user,
            email_type=email_type,
            recipient_email=user.email,
            subject=subject,
            status=EmailLog.STATUS_SENT,
        )
        return True

    except Exception as e:
        logger.error(f'Email send failed [{email_type}] to {user.email}: {e}')
        EmailLog.objects.create(
            user=user,
            email_type=email_type,
            recipient_email=user.email,
            subject=subject,
            status=EmailLog.STATUS_FAILED,
            error_message=str(e),
        )
        return False


def create_notification(user, notification_type, title, message, link='', metadata=None):
    """Create an in-app notification for a user."""
    from apps.notifications.models import Notification
    return Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        link=link,
        metadata=metadata or {},
    )
