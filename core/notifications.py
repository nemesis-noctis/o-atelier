from datetime import datetime
from typing import Any

from django.utils.translation import gettext_noop as _noop

from accounts.models import CustomUser
from .models import Notification

NOTIFICATION_TEMPLATES = {
    "test": _noop("This is a test notification for user {username}"),

    "order_success": _noop("""
    Seu pedido foi realizado com sucesso!
    Logo você será informado(a) se seu pedido foi aceito ou recusado e seu valor total.
    Fique atento às notificações para atualizações.
    """),

    "new_order": _noop(
        """Novo pedido para o usuário {client_name} 
        por BRL: {price_brl}$ USD: {price_usd}$"""),

    "comm_cancelation_client": _noop(
        """O pedido: {uuid} foi cancelado. 
        Verifique a mensagem da artista para mais informações: 
        {message}"""),

    "comm_cancelation_artist": _noop(
        """O pedido: {uuid} do cliente: {client} foi cancelado."""),

    "comm_refusal": _noop(
        """O pedido: {uuid} foi recusado. 
        Verifique a mensagem da artista para mais informações: 
        {message}"""),

    "comm_accepted": _noop(
        """O pedido: {uuid} foi aceito! 
        Seu valor final é de BRL: {price_brl}$ | USD: {price_usd}$. 
        Por favor, realize o pagamento da garantia para prosseguir. 
        Verifique a mensagem da artista para mais informações: 
        {message}"""),

    "comm_update": _noop(
        """O status do pedido: {uuid}, foi atualizado. 
        {previous_stage} -> {current_stage}. 
        """),

    "comm_update_final": _noop(
        """O status do pedido: {uuid}, foi atualizado. 
        {previous_stage} -> {current_stage}.
        Por favor, realize o pagamento do valor restante do pedido para prosseguir.
        """),

    "deposit_confirmation_artist": _noop(
        """O pagamento da garantia do pedido: {uuid} foi realizada. 
        O pedido pode começar a ser produzido.
        """),

    "deposit_confirmation": _noop(
        """O pagamento da garantia do pedido: {uuid} foi realizada com sucesso. 
        O chat agora está liberado para dar feedback ou pedir ajustes.
        A artista logo irá começar o pedido, fique de olho no chat e notificações para atualizações.
        """),

    "full_confirmation_artist": _noop(
        """O pagamento final do pedido: {uuid} foi realizado. 
        O pedido foi finalizado e a arte final já está disponível para o cliente.
        """),

    "full_confirmation": _noop(
        """O pagamento final do pedido: {uuid} foi realizado com sucesso. 
        A arte final já está disponível para download na seção de histórico de pedidos.
        Muito obrigado por escolher fazer a sua commission por aqui e até a próxima!
        """),
}


# LEVELS = ALERT, SUCCESS, MESSAGE

def render_notification(notification: Notification) -> dict[str, str | bool | datetime | Any]:
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


def send_notification_to_client(client: CustomUser, key: str, level: str, context: dict) -> None:
    Notification(user=client,
                 template_key=key,
                 level=level,
                 context=context).save()


def send_notification_to_artist(key: str, level: str, context: dict) -> None:
    Notification(user=CustomUser.objects.get(is_superuser=True),
                 template_key=key,
                 level=level,
                 context=context).save()
