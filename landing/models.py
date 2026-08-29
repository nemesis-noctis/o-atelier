from django.db import models


# Create your models here.
class LandingPage(models.Model):
    artist_name = models.CharField(max_length=24)
    artist_icon = models.ImageField(upload_to="landing", null=True)
    occupation = models.CharField(max_length=40)
    instagram = models.CharField(max_length=24)
    twitter = models.CharField(max_length=24)
    youtube = models.CharField(max_length=24)
    tiktok = models.CharField(max_length=24)
    slots = models.IntegerField()
    comms_status = models.BooleanField()
    bio = models.TextField()

    def __str__(self):
        return "landing_page_info"

    def save(self, *args, **kwargs):
        if self.pk:
            if not self.comms_status:
                self.slots = 0

            else:
                if self.slots == 0:
                    self.comms_status = False

        super().save()


class GalleryTag(models.Model):
    tag = models.CharField(max_length=18)

    def __str__(self):
        return self.tag


class GalleryImage(models.Model):
    title = models.CharField(max_length=24, blank=True)
    image = models.ImageField(upload_to="landing/gallery")
    tag = models.ForeignKey(GalleryTag, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} - {self.tag}"
