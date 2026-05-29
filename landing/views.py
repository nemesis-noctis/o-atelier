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


def gallery_image_filter(request):
    tag_name = request.GET.get("tag", "")
    if tag_name == "all" or tag_name == "":
        gallery_images = GalleryImage.objects.all()
        return render(request, template_name="landing/partials/gallery_images.html",
                      context={"gallery_images": gallery_images})

    else:
        gallery_images = GalleryImage.objects.filter(tag=GalleryTag.objects.get(tag=tag_name))
        return render(request, template_name="landing/partials/gallery_images.html",
                      context={"gallery_images": gallery_images})
