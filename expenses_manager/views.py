from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    a = 5
    b = 10
    # locals() creates a dict() object with all the variables from the local scope. We are passing it to the template
    return render(request, 'index.html', locals())