from django.http import HttpResponse
from django.shortcuts import render

from core.utils import get_landing_data, get_gallery_images_from_tags
from .models import GalleryTag, GalleryImage


# Create your views here.
def index(request) -> HttpResponse:
    gallery_tags = GalleryTag.objects.all()
    gallery_images = GalleryImage.objects.all()
    context = {
        "landing_data": get_landing_data(),
        "gallery_tags": gallery_tags,
        "gallery_images": gallery_images
    }
    return render(request, "landing/index.html", context=context)


def gallery_image_filter(request) -> HttpResponse:
    tag_name = request.GET.get("tag", "")
    return get_gallery_images_from_tags(request, tag_name, "landing/partials/gallery_images.html")
