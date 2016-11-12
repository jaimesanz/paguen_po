# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from expenses_manager.custom_decorators import request_passes_test
from expenses_manager.forms import ViviendaForm, TransferForm
from expenses_manager.utils import create_new_vivienda, user_has_vivienda, \
    get_instructions_from_balance, is_valid_transfer_to_user, \
    is_valid_transfer_monto
from .models import ViviendaUsuario


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
