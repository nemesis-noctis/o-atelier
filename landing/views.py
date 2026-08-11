from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render

from core.utils import get_landing_data, get_gallery_images_from_tags
from .models import GalleryTag, GalleryImage


# Create your views here.
def index(request) -> HttpResponse:
    gallery_tags = cache.get("gallery_tags")
    if not gallery_tags:
        gallery_tags = GalleryTag.objects.all()
        cache.set("gallery_tags", gallery_tags, 600)

    gallery_images = cache.get("gallery_images")
    if not gallery_images:
        gallery_images = GalleryImage.objects.all()
        cache.set("all_gallery_images", gallery_images, 600)

    context = {
        "landing_data": get_landing_data(),
        "gallery_tags": gallery_tags,
        "gallery_images": gallery_images
    }
    return render(request, "landing/index.html", context=context)


def gallery_image_filter(request) -> HttpResponse:
    tag_name = request.GET.get("tag", "")
    return get_gallery_images_from_tags(request, tag_name, "landing/partials/gallery_images.html")
