from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    a = 5
    b = 10
    return render(request, 'index.html', locals())