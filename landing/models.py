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
