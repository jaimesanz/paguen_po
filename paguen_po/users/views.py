# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def login_post_process(request):
    # set session variables here
    request.session['user_has_vivienda'] = request.user.has_vivienda()
    return redirect("home")
