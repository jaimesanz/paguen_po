# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from forms import UserForm
from django.contrib.auth.decorators import login_required
from models import *


def home(request):
	a = 5
	b = 10
	# locals() creates a dict() object with all the variables from the local scope. We are passing it to the template
	return render(request, 'home.html', locals())

@login_required
def login_test(request):
	return render(request, "login_test.html", locals())

@login_required
def invites_list(request):
	# get list of invites for this user
	invites = Invitacion.objects.filter(invitado=request.user)
	return render(request, "invites_list.html", locals())

@login_required
def new_vivienda(request):
	return render(request, "new_vivienda.html", locals())