from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
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


class EditAccountInfoForm(SetPasswordForm):
    email = forms.EmailField(required=False)
    username = forms.CharField(max_length=150, validators=[UnicodeUsernameValidator()])

    class Meta:
        models = get_user_model()
        fields = ("email", "username", "new_password1", "new_password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_fields_classes(self.fields.values())
