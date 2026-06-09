import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as login_user, logout as logout_user, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, \
    PasswordResetCompleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from dotenv import load_dotenv

import accounts.forms as forms
from core.utils import redirect_if_logged, get_landing_data, add_current_data_to_post_if_empty, \
    render_gallery_images_from_tags
from landing.models import GalleryTag, GalleryImage

load_dotenv(settings.BASE_DIR / ".env")


# Create your views here.

@login_required
def user_profile(request):
    return render(request, "accounts/profile/profile.html", context={"landing_data": get_landing_data()})


class GalleryEditorView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request):
        gallery_tags = GalleryTag.objects.all()
        gallery_images = GalleryImage.objects.all()
        context = {
            "gallery_tags": gallery_tags,
            "gallery_images": gallery_images
        }
        return render(request, "accounts/artist/partials/gallery_editor.html", context=context)


class GalleryDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, _type, pk):
        if _type == "tag":
            return render(request, "accounts/artist/partials/gallery_tag_delete_confirmation.html", context={"pk": pk})

        elif _type == "image":
            return render(request, "accounts/artist/partials/gallery_image_delete_confirmation.html",
                          context={"pk": pk})

        else:
            return redirect("gallery_editor")

    def post(self, request, _type, pk):
        if _type == "tag":
            GalleryTag.objects.get(pk=pk).delete()
            return redirect("gallery_editor")

        elif _type == "image":
            GalleryImage.objects.get(pk=pk).delete()
            return redirect("gallery_editor")

        else:
            return redirect("gallery_editor")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def gallery_editor_image_filter(request):
    tag_name = request.GET.get("tag", "")
    all_tags = GalleryTag.objects.all()
    return render_gallery_images_from_tags(request, tag_name, "accounts/artist/partials/gallery_images.html",
                                           all_tags=all_tags)


class LandingPageEditorView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy("login")

    def test_func(self):
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

    def post(self, request):
        landing_data = get_landing_data()
        post_data = add_current_data_to_post_if_empty(request, self.get_current_landing_data_dict(landing_data))
        form = forms.LandingPageEditorForm(post_data.POST, post_data.FILES, instance=landing_data)

        if form.is_valid():
            print(form.cleaned_data)
            form.save()
            messages.success(request, "Dados alterados com sucesso.")
            return render(request, "accounts/artist/partials/landing_page_editor.html",
                          context={"form": form})

        else:

            return render(request, "accounts/artist/partials/landing_page_editor.html",
                          context={"form": form})

    def get(self, request):
        landing_data = get_landing_data()
        form = forms.LandingPageEditorForm(initial=self.get_current_landing_data_dict(landing_data),
                                           instance=landing_data)
        return render(request, "accounts/artist/partials/landing_page_editor.html", context={"form": form})


class ChangeAccountDataView(LoginRequiredMixin, View):
    login_url = reverse_lazy("login")

    def post(self, request):

        current_data = {
            "username": request.user.username,
            "email": request.user.email,
            "new_password1": request.POST.get("old_password", ""),
        }

        post_data = add_current_data_to_post_if_empty(request, current_data).POST
        post_data["new_password2"] = post_data.get("new_password1", "")

        form = forms.EditAccountDataForm(request.user, post_data)
        if form.is_valid():
            data = form.cleaned_data
            request.user.username = data["username"]
            request.user.email = data["email"]
            request.user.save()
            form.save()

            user = authenticate(request, username=data["username"], password=data["new_password1"])
            login_user(request, user)

            messages.success(request, "Dados alterados com sucesso.")
            return render(request, "accounts/partials/change_account_data.html",
                          context={"form": form})

        else:
            return render(request, "accounts/partials/change_account_data.html",
                          context={"form": form})

    def get(self, request):
        form = forms.EditAccountDataForm(user=request.user,
                                         initial={"username": request.user.username, "email": request.user.email})
        return render(request, "accounts/partials/change_account_data.html",
                      context={"form": form})


@login_required()
def logout(request):
    logout_user(request)
    return redirect("landing-page")


##################################################################

@redirect_if_logged
def login(request):
    if request.method == "POST":
        form = forms.LoginForm(request, request.POST)
        if form.is_valid():
            login_user(request, form.get_user())
            return redirect("landing-page")

        else:
            messages.error(request, "Email ou senha inválidos.")
            return render(request, "accounts/login.html", context={"form": form, "landing_data": get_landing_data()})

    form = forms.LoginForm(request)
    return render(request, "accounts/login.html", context={"form": form, "landing_data": get_landing_data()})


@redirect_if_logged
def register(request):
    if request.method == "POST":
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sua conta foi criada com sucesso, prossiga com o login.")
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
