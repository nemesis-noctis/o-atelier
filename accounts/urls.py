from django.urls import path

from . import views

urlpatterns = [
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path("password-recovery", views.PasswordRecoverView.as_view(), name="password-reset"),
    path("password-recovery-confirm/<uidb64>/<token>", views.PasswordRecoveryConfirmView.as_view(),
         name="password_reset_confirm"),
    path("password-recovery-done", views.PasswordRecoveryDoneView.as_view(), name="password_reset_done"),
    path("password-recovery-complete", views.PasswordRecoveryCompleteView.as_view(), name="password_reset_complete")
]
