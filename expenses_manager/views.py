# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from forms import *
from django.contrib.auth.decorators import login_required
from models import *



def home(request):
	# locals() creates a dict() object with all the variables from the local scope. We are passing it to the template
	return render(request, 'home.html', locals())

def about(request):
	return render(request, "about.html", locals())

def error(request):
	return render(request, "error.html", locals())

@login_required
def login_post_process(request):
	# set session variables here
	request.session['user_has_vivienda']=len(ViviendaUsuario.objects.filter(user=request.user))>0
	return HttpResponseRedirect("/home")

@login_required
def user_info(request):
	print "getting"
	u = MyUser.objects.get(id=request.user.id)
	try:
		u.do_something()
		print "a"
	except Exception, e:
		print e
	print "gotit"
	return render(request, "user_info.html", locals())

@login_required
def invites_list(request):
	# get list of pending invites for this user
	invites_in = Invitacion.objects.filter(invitado=request.user, estado="pendiente")
	invites_out = Invitacion.objects.filter(invitado_por__user=request.user, estado="pendiente")
	return render(request, "invites/invites_list.html", locals())

@login_required
def invite_user(request):
	vivienda_usuario = ViviendaUsuario.objects.get(user=request.user)
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
	invite_in = invite.invitado == request.user
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
				invite.save()
				return HttpResponseRedirect("/vivienda")

			invite.reject()
			invite.save()
			# TODO show message saying the invite was accepted or rejected
			return HttpResponseRedirect("/home")

		return render(request, "invites/invite.html", locals())
	elif invite.invitado_por.user==request.user:
		if request.POST:
			ans = request.POST['SubmitButton']
			if ans == "Cancelar":
				invite.cancel()
				invite.save()
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
	vivienda_usuario = ViviendaUsuario.objects.get(user=request.user)
	# TODO show error message if there are 2 viviendausuario (shouldn't happen!)
	roommates = ViviendaUsuario.objects.filter(vivienda=vivienda_usuario.vivienda)
	return render(request, "vivienda.html", locals())

@login_required
def manage_users(request):
	vivienda_usuario = ViviendaUsuario.objects.get(user=request.user)
	return render(request, "manage_users.html", locals())

@login_required
def abandon(request):
	if request.POST:
		get_object_or_404(ViviendaUsuario, user=request.user).delete()
		request.session['user_has_vivienda']=False
	return HttpResponseRedirect("/home")

@login_required
def balance(request):
	vivienda_usuario = ViviendaUsuario.objects.get(user=request.user)
	return render(request, "balance.html", locals())

@login_required
def visualizations(request):
	vivienda_usuario = ViviendaUsuario.objects.get(user=request.user)
	return render(request, "visualizations.html", locals())

@login_required
def gastos(request):
	vivienda_usuario = ViviendaUsuario.objects.get(user=request.user)
	return render(request, "gastos.html", locals())

@login_required
def presupuestos(request):
	vivienda_usuario = ViviendaUsuario.objects.get(user=request.user)
	return render(request, "presupuestos.html", locals())