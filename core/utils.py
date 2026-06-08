from django.core.files import File
from django.http import HttpRequest
from django.shortcuts import redirect
from django.shortcuts import render

from landing.models import GalleryTag, GalleryImage
from landing.models import LandingPage


def redirect_if_logged(func):
    """Redirect to 'landing-page' route if user is logged."""

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("landing-page")
        return func(request, *args, **kwargs)

    return wrapper


def get_landing_data() -> LandingPage:
    """Get landing page and navbar data from db."""
    data = LandingPage.objects.all().order_by("-pk")[0]
    return data


def add_current_data_to_post_if_empty(request, current_data) -> HttpRequest:
    """Add the entered current data to the post request if the data is empty."""
    post_data = request.POST.copy()

    for key, value in current_data.items():
        if key == "artist_icon":
            if key not in request.FILES:
                request.FILES[key] = File(value.file.open(), value.name.replace("landing/", ""))

        elif isinstance(value, bool):
            continue

        else:
            if post_data.get(key, "") == "":
                post_data[key] = value

    request.POST = post_data
    return request


def render_gallery_images_from_tags(request, tag, html_template, all_tags=None):
    """Render gallery imagens from db and return render with the given template."""
    if tag == "all" or tag == "":
        gallery_images = GalleryImage.objects.all()
        return render(request, template_name=html_template,
                      context={"gallery_images": gallery_images, "gallery_tags": all_tags})

    else:
        gallery_images = GalleryImage.objects.filter(tag=GalleryTag.objects.get(tag=tag))
        return render(request, template_name=html_template,
                      context={"gallery_images": gallery_images, "gallery_tags": all_tags})
