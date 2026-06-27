import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as login_user, logout as logout_user, authenticate
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, \
    PasswordResetCompleteView
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect, HttpRequest
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from dotenv import load_dotenv

import accounts.forms as forms
from accounts.models import CustomUser
from core.models import Notification
from core.notifications import render_notification
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
        return render(request, "accounts/profile/notifications.html", context=context)

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
            # TODO: Alterar para o valor certo quando as commissions forem adicionadas
            "comms": "username",
            "spend": "username"
        }

        return users.order_by(orders[order_by if order_by in orders else "username"])

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
