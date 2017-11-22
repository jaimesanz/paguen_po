# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse


@login_required
def get_user_data(request):
    """Endpoint to get user data."""
    return JsonResponse({
        "user": {
            "name": request.user.username
        }
    })
