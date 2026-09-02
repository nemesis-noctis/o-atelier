from celery import shared_task
from django.core.mail import send_mail
from django.utils.translation import gettext_noop as _noop

from accounts.models import CustomUser
from .models import Notification
from .notifications import NOTIFICATION_TEMPLATES


@shared_task
def send_notification_to_client(client: CustomUser, key: str, level: str, context: dict) -> None:
    kwargs = {
        "user": client,
        "template_key": key,
        "level": level,
        "context": context
    }

    template = NOTIFICATION_TEMPLATES.get(key,
                                          (_noop("Erro, O'Atelier"),
                                           _noop("Ocorreu um erro e esta mensagem não pode ser processada.")))
    Notification(**kwargs).save()

    if client.email:
        send_mail(
            from_email=None,
            subject=template[0],
            message=template[1].format(**context),
            recipient_list=[client.email],
            fail_silently=False
        )


@shared_task
def send_notification_to_artist(key: str, level: str, context: dict) -> None:
    artist = CustomUser.objects.get(is_superuser=True)
    Notification(user=artist,
                 template_key=key,
                 level=level,
                 context=context).save()

    template = NOTIFICATION_TEMPLATES.get(key,
                                          (_noop("Erro, O'Atelier"),
                                           _noop("Ocorreu um erro e esta mensagem não pode ser processada.")))
    send_mail(
        from_email=None,
        subject=template[0],
        message=template[1].format(**context),
        recipient_list=[artist.email],
        fail_silently=False
    )
