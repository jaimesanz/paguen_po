# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http.response import JsonResponse


@login_required
def index(request):
    return render(request, "core/index.html", {})


@login_required
def get_user_data(request):
    """Endpoint to get user data."""
    return JsonResponse({
        "user": {
            "name": request.user.username
        }
    })
