from django.urls import path

from . import views

urlpatterns = [
    path("choice", views.commission_choice, name="comms_choice"),
    path("form/<_type>", views.CommissionFormView.as_view(), name="comms_form"),
    path("confirmation/<_type>", views.commission_confirmation, name="comms-confirmation")
]
