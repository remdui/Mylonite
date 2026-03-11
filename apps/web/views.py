from django.http import JsonResponse
from django.shortcuts import render


def health(request):
    return JsonResponse({"status": "ok"})


def home(request):
    return render(
        request,
        "web/home.html",
        {
            "page_title": "Home",
        },
    )
