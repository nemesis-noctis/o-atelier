from django.urls import path

from . import views

urlpatterns = [
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path("logout", views.logout, name="logout"),
    path("password-recovery", views.PasswordRecoverView.as_view(), name="password-reset"),
    path("password-recovery-confirm/<uidb64>/<token>", views.PasswordRecoveryConfirmView.as_view(),
         name="password_reset_confirm"),
    path("password-recovery-done", views.PasswordRecoveryDoneView.as_view(), name="password_reset_done"),
    path("password-recovery-complete", views.PasswordRecoveryCompleteView.as_view(), name="password_reset_complete"),
    path("profile", views.user_profile, name="user_profile"),
    path("change-account-data", views.ChangeAccountDataView.as_view(), name="change_account_data"),
    path("landing-page-editor", views.LandingPageEditorView.as_view(), name="landing_page_editor"),
    path("gallery-editor", views.GalleryEditorView.as_view(), name="gallery_editor"),
    path("gallery-editor-image-filter", views.gallery_editor_image_filter, name="gallery_editor_image_filter"),
    path("gallery-add/<_type>", views.GalleryAddView.as_view(), name="gallery_add"),
    path("gallery-delete/<_type>/<int:pk>", views.GalleryDeleteView.as_view(),
         name="gallery_delete"),
    path("user-manager", views.UserManagerView.as_view(), name="user_manager"),
    path("blocked-user/<b_status>/<int:pk>", views.BlockedUserView.as_view(), name="blocked_user"),
    path("change-user-password", views.ChangeUserPasswordView.as_view(), name="change_user_password"),
    path("notifications", views.NotificationsView.as_view(), name="notifications")
]
