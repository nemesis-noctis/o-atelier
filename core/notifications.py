from django.utils.translation import gettext_noop as _noop

from .models import Notification

NOTIFICATION_TEMPLATES = {
    "test": _noop("This is a test notification for user {username}")
}


def render_notification(notification: Notification):
    template = NOTIFICATION_TEMPLATES.get(notification.template_key,
                                          _noop("Ocorreu um erro e esta mensagem não pode ser processada."))
    message = template.format(**notification.context)
    notification_data = {
        "pk": notification.pk,
        "message": message,
        "level": notification.level,
        "is_read": notification.is_read,
        "created_at": notification.created_at,
    }

    return notification_data
