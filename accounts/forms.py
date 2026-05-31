from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm, \
    PasswordChangeForm
from django.contrib.auth.validators import UnicodeUsernameValidator


def set_fields_classes(fields_values):
    for field in fields_values:
        field.widget.attrs["class"] = "form-control login-register-inputs"


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_fields_classes(self.fields.values())

    def clean_email(self):
        entered_email = self.cleaned_data["email"]
        if get_user_model().objects.filter(email=entered_email, is_active=False).exists():
            raise (forms.ValidationError("Este email foi bloqueado e não pode mais ser usado."))


class LoginForm(AuthenticationForm):
    class Meta:
        model = get_user_model()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_fields_classes(self.fields.values())


class RecoverPasswordEmailForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_fields_classes(self.fields.values())


class NewPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        set_fields_classes(self.fields.values())


class EditAccountDataForm(PasswordChangeForm):
    email = forms.EmailField(required=False)
    username = forms.CharField(required=False, max_length=150, validators=[UnicodeUsernameValidator()])

    class Meta:
        models = get_user_model()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_fields_classes(self.fields.values())

    def clean_username(self):
        entered_username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username=entered_username).exclude(pk=self.user.pk).exists():
            raise (forms.ValidationError("O nome de usuário já existe."))
        return entered_username

    def clean_email(self):
        entered_email = self.cleaned_data["email"]
        if get_user_model().objects.filter(email=entered_email, is_active=False).exclude(
                pk=self.user.pk).exists():
            raise (forms.ValidationError("Este email foi bloqueado e não pode mais ser usado."))
        return entered_email
