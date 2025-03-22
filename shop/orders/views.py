from django.shortcuts import render
from django.http import FileResponse


# Create your views here.

def main(request):
    return FileResponse(open("static/main.pdf", "rb"), content_type="application/pdf")
