from django.contrib import admin

from .models import LandingPage, GalleryTag, GalleryImage

# Register your models here.

admin.site.register(LandingPage)
admin.site.register(GalleryTag)
admin.site.register(GalleryImage)
