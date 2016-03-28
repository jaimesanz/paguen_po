# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from forms import *
from django.contrib.auth.decorators import login_required
from models import *


def home(request):
	# locals() creates a dict() object with all the variables from the local scope. We are passing it to the template
	return render(request, 'home.html', locals())

def login_post_process(request):
	# set session variables here
	request.session['user_has_vivienda']=len(ViviendaUsuario.objects.filter(user=request.user))>0
	return HttpResponseRedirect("/home")

@login_required
def invites_list(request):
	# get list of invites for this user
	invites = Invitacion.objects.filter(invitado=request.user)
	return render(request, "invites_list.html", locals())

@login_required
def nueva_vivienda(request):
	if request.POST:
		form = ViviendaForm(request.POST)
		if form.is_valid():
			# process data
			# save new vivienda
			new_viv = form.save()
			# create new viviendausuario
			vivienda_usuario = ViviendaUsuario(vivienda=new_viv, user=request.user)
			vivienda_usuario.save()
			request.session['user_has_vivienda']=True
			return HttpResponseRedirect("/home")

	vivienda_form = ViviendaForm()
	return render(request, "nueva_vivienda.html", locals())

@login_required
def consultar_vivienda(request):
	# get the user's vivienda
	vivienda_usuario = ViviendaUsuario.objects.get(user=request.user)
	# TODO show error message if there are 2 viviendausuario (shouldn't happen!)
	return render(request, "consultar_vivienda.html", locals())

@login_required
def user_info(request):
	print request.session
	return render(request, "user_info.html", locals())