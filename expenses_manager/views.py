# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from forms import UserForm
from django.contrib.auth.decorators import login_required


def home(request):
	a = 5
	b = 10
	# locals() creates a dict() object with all the variables from the local scope. We are passing it to the template
	return render(request, 'home.html', locals())

@login_required
def login_test(request):
    return render(request, "login_test.html", locals())


# TODO: read this document and see if it's worth using: https://django-registration.readthedocs.org/en/2.0.4/hmac.html#hmac-workflow