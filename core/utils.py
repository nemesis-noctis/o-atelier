from django import forms
from django.core.cache import cache
from django.core.files import File
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render

from landing.models import GalleryTag, GalleryImage
from landing.models import LandingPage


def redirect_if_logged(func):
    """Redirect to 'landing-page' route if user is logged."""

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("landing_page")
        return func(request, *args, **kwargs)

    return wrapper


def get_landing_data() -> LandingPage:
    """Get landing page and navbar data from db."""
    data = LandingPage.objects.all().order_by("-pk")
    if not data:
        landing_fields = {
            "artist_name": "------",
            "occupation": "------",
            "instagram": "------",
            "twitter": "------",
            "youtube": "------",
            "tiktok": "------",
            "slots": 0,
            "comms_status": False,
            "bio": "------"
        }

        data = LandingPage(**landing_fields)
        data.save()
    else:
        data = data[0]
        
    return data


def decrease_comms_slots():
    landing_data = LandingPage.objects.all()[0]
    landing_data.slots -= 1
    landing_data.save()


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


def get_gallery_images_from_tags(request, tag: str, html_template: str, all_tags=None) -> HttpResponse:
    """Get gallery imagens from db and return response with the given template."""
    if tag == "all" or tag == "":

        gallery_images = cache.get("all_gallery_images")
        if not gallery_images:
            gallery_images = GalleryImage.objects.all()
            cache.set("all_gallery_images", gallery_images, 600)

        return render(request, template_name=html_template,
                      context={"gallery_images": gallery_images, "gallery_tags": all_tags})

    else:
        gallery_images = cache.get(f"{tag}_gallery_images")
        if not gallery_images:
            try:
                gallery_images = GalleryImage.objects.filter(tag=GalleryTag.objects.get(tag=tag))
                cache.set(f"{tag}_gallery_images", gallery_images, 600)
            except GalleryTag.DoesNotExist:
                gallery_images = None

        return render(request, template_name=html_template,
                      context={"gallery_images": gallery_images, "gallery_tags": all_tags})


def set_form_field_classes(fields_values):
    """Set HTML classes to each form field for styling."""
    for field in fields_values:
        if isinstance(field.widget, forms.RadioSelect):
            pass

        elif isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = "form-check-input"

        elif isinstance(field, forms.ImageField):
            field.widget.attrs["class"] = "form-control form-control-sm login-register-inputs"

        else:
            field.widget.attrs["class"] = "form-control login-register-inputs"
