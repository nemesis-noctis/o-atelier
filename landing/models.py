from django.db import models


# Create your models here.
class LandingPage(models.Model):
    artist_name = models.CharField(max_length=24)
    artist_icon = models.ImageField(upload_to="landing")
    occupation = models.CharField(max_length=40)
    instagram = models.CharField(max_length=24)
    twitter = models.CharField(max_length=24)
    youtube = models.CharField(max_length=24)
    tiktok = models.CharField(max_length=24)
    slots = models.IntegerField()
    comms_status = models.BooleanField()
    bio = models.TextField()


class GalleryTag(models.Model):
    tag = models.CharField(max_length=18)


class GalleryImage(models.Model):
    title = models.CharField(max_length=24, blank=True)
    image = models.ImageField(upload_to="landing/gallery")
    tag = models.ForeignKey(GalleryTag, on_delete=models.CASCADE)
