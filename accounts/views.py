import json
import os

import mercadopago
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as login_user, logout as logout_user, authenticate
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, \
    PasswordResetCompleteView
from django.db.models import Count
from django.db.models import Q
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView
from dotenv import load_dotenv

import accounts.forms as forms
from accounts.models import CustomUser
from chat.models import Message, MessageImage
from commissions.models import Commission, ProgressImage
from core.models import Notification
from core.notifications import render_notification, send_notification_to_client, send_notification_to_artist
from core.utils import redirect_if_logged, get_landing_data, add_current_data_to_post_if_empty, \
    get_gallery_images_from_tags
from landing.models import GalleryTag, GalleryImage, LandingPage

load_dotenv(settings.BASE_DIR / ".env")


# Create your views here.

@login_required
def user_profile(request) -> HttpResponse:
    new_notifications = False
    if request.user.notifications.filter(is_read=False).exists():
        new_notifications = True

    return render(request, "accounts/profile/profile.html",
                  context={"landing_data": get_landing_data(), "new_notifications": new_notifications})


class PaymentView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def get(self, request, uuid, currency: str) -> HttpResponseRedirect | HttpResponse:
        commission: Commission = request.user.commissions.get(uuid=uuid)

        if (not commission.stage in ["waiting_deposit_payment", "waiting_full_payment"]) or (
                currency not in ["brl", "usd"]):
            return redirect("comms_in_progress")

        amount = round(commission.price_brl / 2, 2) if currency == "brl" else round(commission.price_usd / 2, 2)
        context = {"commission": commission,
                   "currency": currency,
                   "amount": amount}
        return render(request, "accounts/partials/payment.html", context=context)

    def post(self, request, uuid, currency) -> HttpResponseRedirect | HttpResponse:
        commission: Commission = request.user.commissions.get(uuid=uuid)

        if (not commission.stage in ["waiting_deposit_payment", "waiting_full_payment"]) or (
                currency not in ["brl", "usd"]):
            return redirect("comms_in_progress")

        sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {
            'x-idempotency-key': f"comm-{commission.uuid}-deposit" if commission.stage == "waiting_deposit_payment" else f"comm-{commission.uuid}-full"
        }

        data = json.loads(request.body)
        amount = round(commission.price_brl / 2, 2) if currency == "brl" else round(commission.price_usd / 2, 2)

        if data["payment_method_id"] == "pix":
            payment_data = {
                "transaction_amount": amount,
                "payment_method_id": data.get("payment_method_id"),
                "external_reference": f"comm-{commission.uuid}-deposit" if commission.stage == "waiting_deposit_payment" else f"comm-{commission.uuid}-full",
                "payer": {
                    "email": json.loads(data.get("payer")).get("email"),
                },
            }
        else:
            payment_data = {
                "three_d_secure_mode": 'optional',
                "transaction_amount": amount,
                "token": data.get("token"),
                "description": data.get("description"),
                "installments": int(data.get("installments")),
                "payment_method_id": data.get("payment_method_id"),
                "external_reference": f"comm-{commission.uuid}-deposit" if commission.stage == "waiting_deposit_payment" else f"comm-{commission.uuid}-full",
                "payer": {
                    "email": json.loads(data.get("payer")).get("email"),
                    "identification": {
                        "type": json.loads(data.get("payer")).get("identification").get("type"),
                        "number": json.loads(data.get("payer")).get("identification").get("number")
                    },
                },
            }

        payment_response = sdk.payment().create(payment_data, request_options)
        payment = payment_response["response"]
        context = {"commission": commission,
                   "currency": currency,
                   "amount": amount,
                   "payment": payment}
        return render(request, "accounts/partials/payment.html", context=context)


@login_required
def payment_currency_choice(request, uuid) -> HttpResponse:
    commission: Commission = request.user.commissions.get(uuid=uuid)
    if not commission.stage in ["waiting_deposit_payment", "waiting_full_payment"]:
        return redirect("comms_in_progress")

    return render(request, "accounts/partials/payment_currency_choice.html", context={"commission": commission})


class CommChat(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def get(self, request, uuid) -> HttpResponse:
        if request.user.is_superuser:
            commission = Commission.objects.get(uuid=uuid)
        else:
            commission = request.user.commissions.get(uuid=uuid)

        messages = commission.messages.all().order_by("-created_at")

        context = {
            "all_messages": messages,
            "commission": commission,
            "form": forms.SendMessageForm(),
            "image_form": forms.MessageImageForm()
        }
        return render(request, "accounts/partials/comm_chat.html", context=context)


class CommsInProgressDetailsView(LoginRequiredMixin, DetailView):
    login_url = reverse_lazy("login")
    model = Commission
    template_name = "accounts/partials/comms_in_progress_details.html"
    context_object_name = "commission"

    def get_queryset(self):
        if self.request.user.is_superuser:
            commissions = Commission.objects.exclude(Q(stage="finished") | Q(stage="canceled"))
            return commissions

        else:
            commissions = Commission.objects.filter(user=self.request.user).exclude(
                Q(stage="finished") | Q(stage="canceled"))
            return commissions


class CommsInProgressView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def get(self, request) -> HttpResponse:
        if request.user.is_superuser:
            comms_in_progress = Commission.objects.exclude(Q(stage="finished") | Q(stage="canceled")).order_by(
                "-created_at")
        else:
            comms_in_progress: Commission = request.user.commissions.exclude(
                Q(stage="finished") | Q(stage="canceled")).order_by("-created_at")

        context = {
            "commissions": comms_in_progress,
            "count": comms_in_progress.count()
        }

        return render(request, "accounts/partials/comms_in_progress.html", context=context)


class CommissionNextStageView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser

    def set_commission_to_next_stage(self, commission: Commission, commit: bool) -> str:
        stages = ["sketch", "lineart", "flat_colour", "render"]
        current_stage = commission.stage

        next_stage = "waiting_full_payment" if current_stage == commission.final_stage else stages[
            stages.index(current_stage) + 1]
        commission.stage = next_stage
        next_stage = commission.get_stage_display()

        if commit:
            commission.save()
        else:
            commission.stage = current_stage

        return next_stage

    def get(self, request, uuid) -> HttpResponse:
        commission = Commission.objects.get(uuid=uuid)
        form = forms.NextStageForm()
        next_stage = self.set_commission_to_next_stage(commission, commit=False)
        context = {
            "commission": commission,
            "form": form,
            "next_stage": next_stage
        }
        return render(request, "accounts/artist/partials/next_stage_confirmation.html", context=context)

    def post(self, request, uuid):
        form = forms.NextStageForm(request.POST, request.FILES)
        commission = Commission.objects.get(uuid=uuid)

        if form.is_valid():
            previous_stage = commission.get_stage_display()
            next_stage = self.set_commission_to_next_stage(commission, commit=True)
            instance: ProgressImage = form.save(commit=False)
            instance.commission = commission
            instance.stage = previous_stage
            instance.save()

            sys_message_image = MessageImage(image=instance.image)
            sys_message_image.save()
            sys_message = Message(content=_(commission.get_stage_display()), commission=commission,
                                  image=sys_message_image).save()

            notification_key = "comm_update_final" if commission.stage == "waiting_full_payment" else "comm_update"
            send_notification_to_client(commission.user, notification_key, "MESSAGE",
                                        context={"uuid": str(commission.uuid),
                                                 "previous_stage": previous_stage.title(),
                                                 "current_stage": next_stage.title()})

            return redirect("comms_in_progress")
        else:
            next_stage = self.set_commission_to_next_stage(commission, commit=False)
            context = {
                "commission": commission,
                "form": form,
                "next_stage": next_stage
            }
            return render(request, "accounts/artist/partials/next_stage_confirmation.html", context=context)


class AcceptCommissionView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser

    def get(self, request, uuid) -> HttpResponse:
        comm_to_accept = Commission.objects.get(uuid=uuid)
        form = forms.ReasonForm()
        form.fields["new_price_brl"].initial = comm_to_accept.price_brl
        form.fields["new_price_usd"].initial = comm_to_accept.price_usd
        context = {
            "commission": comm_to_accept,
            "form": form
        }
        return render(request, "accounts/artist/partials/accept_confirmation.html", context=context)

    def post(self, request, uuid):
        form = forms.ReasonForm(request.POST)
        comm_to_accept = Commission.objects.get(uuid=uuid)

        if form.is_valid():
            comm_to_accept.stage = "waiting_deposit_payment"
            comm_to_accept.price_brl = form.cleaned_data["new_price_brl"]
            comm_to_accept.price_usd = form.cleaned_data["new_price_usd"]
            comm_to_accept.save()
            accept_message = form.cleaned_data["reason"]

            send_notification_to_client(comm_to_accept.user, "comm_accepted", "SUCCESS",
                                        context={"message": accept_message, "uuid": str(comm_to_accept.uuid),
                                                 "price_brl": comm_to_accept.price_brl,
                                                 "price_usd": comm_to_accept.price_usd})

            return redirect("comms_in_progress")
        else:
            context = {
                "commission": comm_to_accept,
                "form": form
            }
            return render(request, "accounts/artist/partials/accept_confirmation.html", context=context)


class CancelCommissionView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def get(self, request, uuid) -> HttpResponse:
        if request.user.is_superuser:
            comm_to_cancel = Commission.objects.get(uuid=uuid)
            form = forms.ReasonForm()
            context = {
                "commission": comm_to_cancel,
                "form": form
            }
            return render(request, "accounts/partials/cancel_confirmation.html", context=context)

        else:
            comm_to_cancel = request.user.commissions.get(uuid=uuid)
            context = {
                "commission": comm_to_cancel
            }
            return render(request, "accounts/partials/cancel_confirmation.html", context=context)

    def post(self, request, uuid) -> HttpResponseRedirect | HttpResponse:
        if request.user.is_superuser:
            form = forms.ReasonForm(request.POST)
            comm_to_cancel = Commission.objects.get(uuid=uuid)

            if form.is_valid():
                comm_original_stage = comm_to_cancel.stage
                comm_to_cancel.stage = "canceled"
                comm_to_cancel.progress_image.all().delete()
                comm_to_cancel.reference_images.all().delete()
                comm_to_cancel.finished_at = timezone.now()
                comm_to_cancel.save()
                cancellation_reason = form.cleaned_data["reason"]

                notification_key = "comm_refusal" if comm_original_stage == "waiting_confirmation" else "comm_cancelation_client"
                send_notification_to_client(comm_to_cancel.user, notification_key, "ALERT",
                                            context={"message": cancellation_reason, "uuid": str(comm_to_cancel.uuid)})

                return redirect("comms_in_progress")
            else:
                context = {
                    "commission": comm_to_cancel,
                    "form": form
                }
                return render(request, "accounts/partials/cancel_confirmation.html", context=context)

        else:
            comm_to_cancel = request.user.commissions.get(uuid=uuid)
            comm_to_cancel.stage = "canceled"
            comm_to_cancel.progress_image.all().delete()
            comm_to_cancel.reference_images.all().delete()
            comm_to_cancel.finished_at = timezone.now()
            comm_to_cancel.save()

            send_notification_to_artist("comm_cancelation_artist", "ALERT",
                                        context={"uuid": str(comm_to_cancel.uuid),
                                                 "client": comm_to_cancel.user.username})

            return redirect("comms_in_progress")


class CommsHistoryView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def get(self, request) -> HttpResponse:
        if request.user.is_superuser:
            completed_commissions = Commission.objects.filter(Q(stage="finished") | Q(stage="canceled")).order_by(
                "-created_at")

        else:
            completed_commissions: Commission = request.user.commissions.filter(
                Q(stage="finished") | Q(stage="canceled")).order_by("-created_at")

        for commission in completed_commissions:
            if commission.stage == "finished":
                commission.final_image = commission.progress_image.get(stage=commission.final_stage)

        context = {
            "commissions": completed_commissions,
            "count": completed_commissions.count()
        }
        return render(request, "accounts/partials/comms_history.html", context=context)


class NotificationsView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def get(self, request) -> HttpResponse:
        notifications: QuerySet[Notification] = request.user.notifications.all().order_by("-created_at")
        rendered_notifications = []
        if notifications:
            for notification in notifications:
                rendered_notification = render_notification(notification)
                rendered_notifications.append(rendered_notification)

        context = {
            "notifications": rendered_notifications
        }
        return render(request, "accounts/partials/notifications.html", context=context)

    def post(self, request) -> HttpResponseRedirect:
        read_all = request.POST.get("read_all", "")
        if not read_all == "":
            request.user.notifications.all().update(is_read=True)

        notification_pk = request.POST.get("pk", "")
        if not notification_pk == "":
            notification = request.user.notifications.get(pk=notification_pk)
            notification.is_read = True
            notification.save()

        # notification icon reloader
        messages.success(request, message="None")
        return redirect("notifications")


class UserManagerView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser

    def order_users(self, users: QuerySet[CustomUser], order_by: str) -> QuerySet[CustomUser]:
        orders = {
            "username": "username",
            "date": "date_joined",
            "active": "is_active",
            "comms": "username",
        }

        if not order_by == "comms":
            ordered = users.order_by(orders[order_by if order_by in orders else "username"])
        else:
            ordered = users.annotate(comms_count=Count("commissions")).order_by("-comms_count")

        return ordered

    def get(self, request) -> HttpResponse:
        username_search = request.GET.get("username_search", "")
        all_users = CustomUser.objects.all().filter(username__icontains=username_search, is_superuser=False)
        users_count = all_users.count()
        order_by = request.GET.get("order_by", "")
        context = {
            "users": self.order_users(all_users, order_by),
            "users_count": users_count,
            "order_by": order_by,
            "username_search": username_search,
        }
        return render(request, "accounts/artist/partials/user_manager.html", context=context)


class ChangeUserPasswordView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser

    def get_user_pk(self, request) -> CustomUser:
        if request.method == "GET":
            user_pk = request.GET.get("user_pk", "")
            return CustomUser.objects.get(pk=user_pk)
        else:
            user_pk = request.POST.get("user_pk", "")
            return CustomUser.objects.get(pk=user_pk)

    def get(self, request) -> HttpResponse:
        user = self.get_user_pk(request)
        context = {
            "user_": user,
            "form": forms.NewPasswordForm(user)
        }
        return render(request, "accounts/artist/partials/change_user_password.html", context=context)

    def post(self, request) -> HttpResponse:
        user = self.get_user_pk(request)
        form = forms.NewPasswordForm(user, request.POST)
        context = {
            "user_": user,
            "form": form
        }
        if form.is_valid():
            form.save()
            messages.success(request, _("Senha alterada com sucesso."))
            return render(request, "accounts/artist/partials/change_user_password.html", context=context)

        else:
            return render(request, "accounts/artist/partials/change_user_password.html", context=context)


class BlockedUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser

    def get(self, request, b_status, pk):
        return render(request, f"accounts/artist/partials/user_block_confirmation.html",
                      context={"b_status": b_status, "pk": pk})

    def post(self, request, b_status, pk):
        user = CustomUser.objects.get(pk=pk)
        user.is_active = False if b_status == "block" else True
        user.save()
        return redirect("user_manager")


class GalleryEditorView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser

    def get(self, request) -> HttpResponse:
        gallery_tags = GalleryTag.objects.all()
        gallery_images = GalleryImage.objects.all()
        context = {
            "gallery_tags": gallery_tags,
            "gallery_images": gallery_images,
            "add_tag_form": forms.AddTagToGalleryForm,
            "add_image_form": forms.AddImageToGalleryForm
        }
        return render(request, "accounts/artist/partials/gallery_editor.html", context=context)


class GalleryAddView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser

    def post(self, request, _type) -> HttpResponseRedirect:
        form = None

        if _type == "image":
            form = forms.AddImageToGalleryForm(request.POST, request.FILES)

        elif _type == "tag":
            form = forms.AddTagToGalleryForm(request.POST)

        if form is not None:
            if form.is_valid():
                form.save()

        return redirect("gallery_editor")


class GalleryDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser

    def get(self, request, _type, pk) -> HttpResponse | HttpResponseRedirect:
        if _type in {"image", "tag"}:
            return render(request, f"accounts/artist/partials/gallery_{_type}_delete_confirmation.html",
                          context={"pk": pk})
        else:
            return redirect("gallery_editor")

    def post(self, request, _type, pk) -> HttpResponseRedirect:
        if _type == "tag":
            GalleryTag.objects.get(pk=pk).delete()

        elif _type == "image":
            GalleryImage.objects.get(pk=pk).delete()

        return redirect("gallery_editor")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def gallery_editor_image_filter(request) -> HttpResponse:
    tag_name = request.GET.get("tag", "")
    all_tags = GalleryTag.objects.all()
    return get_gallery_images_from_tags(request, tag_name, "accounts/artist/partials/gallery_images.html",
                                        all_tags=all_tags)


class LandingPageEditorView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self) -> bool | None:
        return self.request.user.is_superuser

    def get_current_landing_data_dict(self, landing_data) -> dict:
        current_data = {
            "artist_name": landing_data.artist_name,
            "artist_icon": landing_data.artist_icon,
            "occupation": landing_data.occupation,
            "instagram": landing_data.instagram,
            "twitter": landing_data.twitter,
            "youtube": landing_data.youtube,
            "tiktok": landing_data.tiktok,
            "slots": landing_data.slots,
            "comms_status": landing_data.comms_status,
            "bio": landing_data.bio,
        }
        return current_data

    def post(self, request) -> HttpResponse:
        landing_data: LandingPage = get_landing_data()
        post_data: HttpRequest = add_current_data_to_post_if_empty(request,
                                                                   self.get_current_landing_data_dict(landing_data))
        form = forms.LandingPageEditorForm(post_data.POST, post_data.FILES, instance=landing_data)

        if form.is_valid():
            form.save()
            messages.success(request, _("Dados alterados com sucesso."))
            return render(request, "accounts/artist/partials/landing_page_editor.html",
                          context={"form": form})

        else:
            return render(request, "accounts/artist/partials/landing_page_editor.html",
                          context={"form": form})

    def get(self, request):
        landing_data: LandingPage = get_landing_data()
        form = forms.LandingPageEditorForm(initial=self.get_current_landing_data_dict(landing_data),
                                           instance=landing_data)
        return render(request, "accounts/artist/partials/landing_page_editor.html", context={"form": form})


class ChangeAccountDataView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def post(self, request) -> HttpResponse:
        current_data = {
            "username": request.user.username,
            "email": request.user.email,
            "new_password1": request.POST.get("old_password", ""),
        }

        post_data: HttpRequest = add_current_data_to_post_if_empty(request, current_data).POST
        post_data["new_password2"] = post_data.get("new_password1", "")

        form = forms.EditAccountDataForm(request.user, post_data)
        if form.is_valid():
            data = form.cleaned_data
            request.user.username = data["username"]
            request.user.email = data["email"]
            request.user.save()
            form.save()

            user: AbstractBaseUser | None = authenticate(request, username=data["username"],
                                                         password=data["new_password1"])
            login_user(request, user)

            messages.success(request, _("Dados alterados com sucesso."))
            return render(request, "accounts/partials/change_account_data.html",
                          context={"form": form})

        else:
            return render(request, "accounts/partials/change_account_data.html",
                          context={"form": form})

    def get(self, request) -> HttpResponse:
        form = forms.EditAccountDataForm(user=request.user,
                                         initial={"username": request.user.username, "email": request.user.email})
        return render(request, "accounts/partials/change_account_data.html",
                      context={"form": form})


@login_required()
def logout(request) -> HttpResponseRedirect:
    logout_user(request)
    return redirect("landing_page")


##################################################################

@redirect_if_logged
def login(request) -> HttpResponseRedirect | HttpResponse:
    if request.method == "POST":
        form = forms.LoginForm(request, request.POST)
        if form.is_valid():
            login_user(request, form.get_user())
            return redirect("landing_page")

        else:
            messages.error(request, _("Nome de usuário ou senha inválidos."))
            return render(request, "accounts/login.html", context={"form": form, "landing_data": get_landing_data()})

    form = forms.LoginForm(request)
    return render(request, "accounts/login.html", context={"form": form, "landing_data": get_landing_data()})


@redirect_if_logged
def register(request) -> HttpResponseRedirect | HttpResponse:
    if request.method == "POST":
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Sua conta foi criada com sucesso, prossiga com o login."))
            return redirect("login")
        else:
            return render(request, "accounts/register.html", context={"form": form, "landing_data": get_landing_data()})

    form = forms.RegisterForm()
    return render(request, "accounts/register.html", context={"form": form, "landing_data": get_landing_data()})


#############################################################################

class PasswordRecoverView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/emails/password_reset_email.txt"
    from_email = os.getenv("EMAIL_HOST")
    form_class = forms.RecoverPasswordEmailForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_data"] = get_landing_data()
        return context


class PasswordRecoveryConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = forms.NewPasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_data"] = get_landing_data()
        return context


class PasswordRecoveryDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_data"] = get_landing_data()
        return context


class PasswordRecoveryCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["landing_data"] = get_landing_data()
        return context
