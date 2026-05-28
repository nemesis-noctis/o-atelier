from django.shortcuts import render

from core.utils import get_landing_data
from .models import GalleryTag, GalleryImage


# Create your views here.
def index(request):
    gallery_tags = GalleryTag.objects.all()
    gallery_images = GalleryImage.objects.all()
    context = {
        "data": get_landing_data(),
        "gallery_tags": gallery_tags,
        "gallery_images": gallery_images
    }
    return render(request, "landing/index.html", context=context)
