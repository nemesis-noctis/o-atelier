from django.urls import path

from . import views

urlpatterns = [
    path("image-receiver", views.receive_image_upload, name="image_receiver")
]
