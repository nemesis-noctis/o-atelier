from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="landing_page"),
    path("gallery-image-filter", views.gallery_image_filter, name="gallery_image_filter")
]
