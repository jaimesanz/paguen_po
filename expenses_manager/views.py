# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from forms import *
from django.contrib.auth.decorators import login_required
from models import *
from django.forms.models import model_to_dict


def home(request):
	# locals() creates a dict() object with all the variables from the local scope. We are passing it to the template
	return render(request, 'home.html', locals())

def about(request):
	return render(request, "about.html", locals())

def error(request):
	return render(request, "error.html", locals())

######################################################
# from here on, everything must have @login_required
######################################################

@login_required
def login_post_process(request):
	# set session variables here
	request.session['user_has_vivienda'] = request.user.has_vivienda()
	return HttpResponseRedirect("/home")

@login_required
def user_info(request):
	return render(request, "user_info.html", locals())

@login_required
def invites_list(request):
	# get list of pending invites for this user
	invites_in, invites_out = request.user.get_invites()
	return render(request, "invites/invites_list.html", locals())

@login_required
def invite_user(request):
	vivienda_usuario = request.user.get_vu()
	if request.POST:
		post = request.POST.copy()
		post['invitado_por']=vivienda_usuario
		form = InvitacionForm(post)
		if form.is_valid():
			# TODO check that no user with that mail is already in the Vivienda
			if post['email']==request.user.email:
				# TODO show message "you cant invite yourself!"
				return HttpResponseRedirect("/vivienda/")
			invited_user = User.objects.filter(email=post['email']).first()
			if invited_user is not None:
				invite = Invitacion(email=post['email'], invitado_por=vivienda_usuario, invitado=invited_user)
				# TODO send email with link to register
			else:
				invite = Invitacion(email=post['email'], invitado_por=vivienda_usuario)
				# TODO send email with link accept/decline
			invite.save()
			return HttpResponseRedirect("/home")
		else:
			return HttpResponseRedirect("/about")
	invite_form = InvitacionForm()
	return render(request, "invites/invite_user.html", locals())

@login_required
def invite(request, invite_id):
	# TODO add custom error 404 page
	invite = get_object_or_404(Invitacion, id=invite_id)
	invite_in = invite.is_invited_user(request.user)
	if invite_in:
		if request.POST:
			ans = request.POST['SubmitButton']
			if ans == "Aceptar":
				if request.session['user_has_vivienda']:
					# user can't have 2 viviendas
					# TODO show message saying he must leave the current vivienda before joining another
					return HttpResponseRedirect("/error")
				new_vivienda_usuario = invite.accept()
				request.session['user_has_vivienda']=True
				new_vivienda_usuario.save()
				return HttpResponseRedirect("/vivienda")

			invite.reject()
			# TODO show message saying the invite was accepted or rejected
			return HttpResponseRedirect("/home")

		return render(request, "invites/invite.html", locals())
	elif invite.is_invited_by_user(request.user):
		if request.POST:
			ans = request.POST['SubmitButton']
			if ans == "Cancelar":
				invite.cancel()
				return HttpResponseRedirect("/invites_list")

		return render(request, "invites/invite.html", locals())
	else:
		# redirect to page showing message "restricted" 
		return HttpResponseRedirect("/error")

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
			return HttpResponseRedirect("/vivienda")

	vivienda_form = ViviendaForm()
	return render(request, "nueva_vivienda.html", locals())

@login_required
def vivienda(request):
	# get the user's vivienda
	vivienda_usuario = request.user.get_vu()
	# TODO show error message if there are 2 viviendausuario (shouldn't happen!)
	roommates = request.user.get_roommates()
	return render(request, "vivienda.html", locals())

@login_required
def manage_users(request):
	vivienda_usuario = request.user.get_vu()
	return render(request, "manage_users.html", locals())

@login_required
def abandon(request):
	if request.POST:
		get_object_or_404(ViviendaUsuario, user=request.user, estado="activo").leave()
		request.session['user_has_vivienda']=False
	return HttpResponseRedirect("/home")

@login_required
def nuevo_gasto(request):
	vivienda_usuario = request.user.get_vu()
	if request.POST:
		form = GastoForm(request.POST)
		if form.is_valid():
			# set the user who created this
			nuevo_gasto = form.save(commit=False)
			nuevo_gasto.creado_por = request.user.get_vu()
			nuevo_gasto.save()
			# check if it's paid
			if request.POST.get("is_paid", None):
				nuevo_gasto.pagar(request.user)
			# TODO poner mensaje explicando que se agregó con éxito
			return HttpResponseRedirect("/gastos")
		else:
			# TODO redirect to error
			pass
	return HttpResponseRedirect("/gastos")

@login_required
def balance(request):
	vivienda_usuario = request.user.get_vu()
	return render(request, "balance.html", locals())

@login_required
def visualizations(request):
	vivienda_usuario = request.user.get_vu()
	return render(request, "visualizations.html", locals())

@login_required
def gastos(request):
	vivienda_usuario = request.user.get_vu()
	# get list of gastos
	gastos_pendientes_list, gastos_pagados_list = vivienda_usuario.get_gastos_vivienda()
	gasto_form = GastoForm()
	return render(request, "gastos.html", locals())

@login_required
def detalle_gasto(request, gasto_id):
	# TODO retrict access!
	vivienda_usuario = request.user.get_vu()
	gasto = get_object_or_404(Gasto, id=gasto_id)
	if not gasto.allow_user(request.user):
		# TODO show error message
		return HttpResponseRedirect("/error")
	gasto_form = GastoForm(model_to_dict(gasto))
	if request.POST:
		gasto.pagar(request.user)
	return render(request, "detalle_gasto.html", locals())

@login_required
def presupuestos(request):
	vivienda_usuario = request.user.get_vu()
	return render(request, "presupuestos.html", locals())