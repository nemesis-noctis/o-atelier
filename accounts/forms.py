from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm, \
    PasswordChangeForm
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.forms import ModelForm
from django.utils.translation import gettext as _

from core.utils import set_form_field_classes
from landing.models import LandingPage, GalleryTag, GalleryImage


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_form_field_classes(self.fields.values())

    def clean_email(self):
        entered_email = self.cleaned_data["email"]
        if get_user_model().objects.filter(email=entered_email, is_active=False).exists():
            raise (forms.ValidationError(_("Este email foi bloqueado e não pode mais ser usado.")))


class LoginForm(AuthenticationForm):
    class Meta:
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_form_field_classes(self.fields.values())


class RecoverPasswordEmailForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_form_field_classes(self.fields.values())


class NewPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        set_form_field_classes(self.fields.values())


class EditAccountDataForm(PasswordChangeForm):
    email = forms.EmailField(required=False)
    username = forms.CharField(required=False, max_length=150, validators=[UnicodeUsernameValidator()])

    class Meta:
        models = get_user_model()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_form_field_classes(self.fields.values())

    def clean_username(self):
        entered_username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username=entered_username).exclude(pk=self.user.pk).exists():
            raise (forms.ValidationError(_("O nome de usuário já existe.")))
        return entered_username

    def clean_email(self):
        entered_email = self.cleaned_data["email"]
        if get_user_model().objects.filter(email=entered_email, is_active=False).exclude(
                pk=self.user.pk).exists():
            raise (forms.ValidationError(_("Este email foi bloqueado e não pode mais ser usado.")))
        return entered_email


class LandingPageEditorForm(ModelForm):
    class Meta:
        model = LandingPage
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_form_field_classes(self.fields.values())
        bio_field = self.fields["bio"]
        bio_field.widget.attrs["class"] = "form-control landing-editor-textarea"
        bio_field.widget.attrs["style"] = "height: 128px;"


class AddImageToGalleryForm(ModelForm):
    class Meta:
        model = GalleryImage
        fields = ["image", "tag"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_form_field_classes(self.fields.values())


class AddTagToGalleryForm(ModelForm):
    class Meta:
        model = GalleryTag
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "align-middle",
                                  "style": "width: 124px;border-radius: 30px;border-top-right-radius: 0;border-bottom-right-radius: 0;border: 1px inset #69A7FC;padding: 1px 10px;",
                                  "placeholder": _("Adicionar Tag")}
