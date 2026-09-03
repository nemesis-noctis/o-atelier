from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.utils.translation import gettext as _

from chat.models import Message
from core.tasks import send_notification_to_artist, send_notification_to_client
from .models import Commission
from .models import ProgressImage


@shared_task(autoretry_for=(IntegrityError,), max_retries=10, default_retry_delay=30)
def update_commission(commission: Commission):
    prev_comm_stage = commission.stage
    commission.stage = "sketch" if prev_comm_stage == "waiting_deposit_payment" else "finished"
    with transaction.atomic():
        if prev_comm_stage == "waiting_full_payment":
            commission.finished_at = timezone.now()
            final_image_object = commission.progress_image.get(stage=commission.final_stage)
            final_image = ContentFile(final_image_object.image.read(), final_image_object.image.name)
            commission.progress_image.all().delete()
            commission.messages.all().delete()
            commission.reference_images.all().delete()
            ProgressImage(commission=commission, image=final_image, stage=commission.final_stage).save()

        commission.save()

        if prev_comm_stage == "waiting_deposit_payment":
            sys_message = Message(content=_(commission.get_stage_display()), commission=commission).save()

        artist_key = "deposit_confirmation_artist" if prev_comm_stage == "waiting_deposit_payment" else "full_confirmation_artist"
        client_key = "deposit_confirmation" if prev_comm_stage == "waiting_deposit_payment" else "full_confirmation"

        send_notification_to_artist.delay_on_commit(key=artist_key, level="SUCCESS",
                                                    context={"uuid": str(commission.uuid)})
        send_notification_to_client.delay_on_commit(commission.user.id, client_key, "SUCCESS",
                                                    context={"uuid": str(commission.uuid)})
