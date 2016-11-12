# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from core.custom_decorators import request_passes_test
from core.forms import ViviendaForm, TransferForm, InvitacionForm
from core.utils import create_new_vivienda, user_has_vivienda, \
    get_instructions_from_balance, is_valid_transfer_to_user, \
    is_valid_transfer_monto
from .models import ViviendaUsuario, Invitacion


@login_required
def vivienda(request):
    vivienda_usuario = request.user.get_vu()
    roommates = request.user.get_roommates()
    return render(request, "vivienda/vivienda.html", locals())


@login_required
def nueva_vivienda(request):
    if request.POST:
        if request.user.has_vivienda():
            messages.error(
                request,
                "Solo puede pertenecer a una Vivienda.")
            return redirect("vivienda")
        form = ViviendaForm(request.POST)
        if form.is_valid():
            # process data
            # save new vivienda
            new_viv = create_new_vivienda(form)
            # create new viviendausuario
            vivienda_usuario = ViviendaUsuario(
                vivienda=new_viv, user=request.user)
            vivienda_usuario.save()
            request.session['user_has_vivienda'] = True
            messages.success(
                request,
                "¡Vivienda creada con éxito! "
                "Haga click en el botón de información para comenzar a "
                "utilizar la aplicación.")
            return redirect("vivienda")

    vivienda_form = ViviendaForm()
    return render(request, "vivienda/nueva_vivienda.html", locals())


@login_required
def user_info(request):
    return render(request, "user_info.html", locals())


@login_required
def manage_users(request):
    vivienda_usuario = request.user.get_vu()
    return render(request, "vivienda/manage_users.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def balance(request):
    vivienda = request.user.get_vivienda()
    users_disbalance = vivienda.get_disbalance_dict()
    instructions = get_instructions_from_balance(users_disbalance)
    form = TransferForm()
    form.fields["user"].queryset = request.user.get_roommates_users()
    return render(request, "vivienda/balance.html", locals())


@login_required
def abandon(request):
    if request.POST:
        vu = get_object_or_404(
            ViviendaUsuario, user=request.user, estado="activo")
        vu.leave()
        request.session['user_has_vivienda'] = False
    return redirect("home")


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def transfer(request):
    if request.POST:

        # validate user_id in POST
        user, msg = is_valid_transfer_to_user(
            request.POST.get("user", None),
            request.user)

        if user is None:
            # there are errors
            messages.error(request, msg)
            return redirect("transfer")

        # validate monto_raw in POST
        monto, msg = is_valid_transfer_monto(request.POST.get("monto", None))
        if monto is None:
            # there are errors
            messages.error(request, msg)
            return redirect("transfer")

        pos, neg = request.user.transfer(user, monto)
        if pos is not None and neg is not None:
            messages.success(
                request,
                "Transferencia realizada con éxito.")
            return redirect("balance")
        else:
            messages.error(
                request,
                "se produjo un error procesando la transferencia.")
            return redirect("transfer")

    form = TransferForm()
    form.fields["user"].queryset = request.user.get_roommates_users()
    return render(request, "transfer.html", locals())


@login_required
def invites_list(request):
    # get list of pending invites for this user
    invites_in, invites_out = request.user.get_invites()
    return render(request, "invites/invites_list.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def invite_user(request):
    vivienda_usuario = request.user.get_vu()
    if request.POST:
        post = request.POST.copy()
        post['invitado_por'] = vivienda_usuario
        form = InvitacionForm(post)
        if form.is_valid():
            # TODO check that no user with that mail is already in the Vivienda
            if post['email'] == request.user.email:
                messages.error(request, "¡No puede invitarse a usted mismo!")
                return redirect("vivienda")
            invited_user = User.objects.filter(email=post['email']).first()
            if invited_user is not None:
                invite = Invitacion(
                    email=post['email'],
                    invitado_por=vivienda_usuario,
                    invitado=invited_user)
                # TODO send email with link to register
            else:
                invite = Invitacion(
                    email=post['email'],
                    invitado_por=vivienda_usuario)
                # TODO send email with link accept/decline
            invite.save()
            return redirect("invites_list")
        else:
            return redirect("about")
    invite_form = InvitacionForm()
    return render(request, "invites/invite_user.html", locals())


@login_required
def invite(request, invite_id):
    invite = get_object_or_404(Invitacion, id=invite_id)
    invite_in = invite.is_invited_user(request.user)
    if invite_in:
        if invite.is_cancelled():
            return redirect("error")
        if request.POST:
            ans = request.POST['SubmitButton']
            if ans == "Aceptar":
                if request.user.has_vivienda():
                    messages.error(
                        request,
                        """Usted ya pertenece a una vivienda. Para aceptar la
                         invitación debe abandonar su vivienda actual.
                        """)
                    return redirect("error")
                invite.accept()
                request.session['user_has_vivienda'] = True
                messages.success(request, "La invitación fue aceptada.")
                return redirect("vivienda")
            elif ans == "Declinar":
                invite.reject()
                messages.success(request, "La invitación fue rechazada.")
                return redirect("home")
            messages.error(request, "Hubo un error al procesar la invitación")
            return redirect("error")

        return render(request, "invites/invite.html", locals())
    elif invite.is_invited_by_user(request.user):
        if request.POST:
            ans = request.POST['SubmitButton']
            if ans == "Cancelar":
                invite.cancel()
                return redirect("invites_list")

        return render(request, "invites/invite.html", locals())
    else:
        # redirect to page showing message "restricted"
        return redirect("error")
