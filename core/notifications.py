from django.utils.translation import gettext_noop as _noop

from accounts.models import CustomUser
from .models import Notification

NOTIFICATION_TEMPLATES = {
    "test": _noop("This is a test notification for user {username}"),
    "order_success": _noop("""
    Seu pedido foi realizado com sucesso!
    Logo você será informado(a) se seu pedido foi aceito ou recusado e seu valor final.
    Fique atento às notificações para atualizações.
    """),
    "new_order": _noop("Novo pedido para o usuário {client_name} por BRL: {price_brl}$ USD: {price_usd}$")
}


def render_notification(notification: Notification):
    # TODO: Ajustar quando adicionar o idioma inglês pro site.
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


def send_notification_to_client(client, key, level, context):
    Notification(user=client,
                 template_key=key,
                 level=level,
                 context=context).save()


def send_notification_to_artist(key, level, context):
    Notification(user=CustomUser.objects.get(is_superuser=True),
                 template_key=key,
                 level=level,
                 context=context).save()
