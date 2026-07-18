# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render

from accounts.forms import MessageImageForm
from .models import MessageImage


def receive_image_upload(request):
    if request.method == "POST":
        form = MessageImageForm(request.POST, request.FILES)
        if form.is_valid():
            image: MessageImage = form.save()
            return render(request, "chat/partials/img_upload_preview_and_id.html", context={"image": image})
        
    return HttpResponse()
