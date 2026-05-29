from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="landing-page"),
    path("gallery-image-filter", views.gallery_image_filter, name="gallery-image-filter")
]
