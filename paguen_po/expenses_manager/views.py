# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect


def home(request):
    if request.user.is_authenticated() and request.user.has_vivienda():
        return redirect("vivienda")
    return render(request, 'general/home.html', locals())


def about(request):
    return render(request, "general/about.html", locals())


def error(request):
    return render(request, "general/error.html", locals())
