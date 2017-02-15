# -*- coding: utf-8 -*-
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from core.custom_decorators import request_passes_test
from core.utils import user_has_vivienda
from .forms import UserIsOutForm
from .models import UserIsOut


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def vacations(request):
    vacations = UserIsOut.objects.filter(
        vivienda_usuario__vivienda=request.user.get_vivienda(),
        vivienda_usuario__estado="activo")
    return render(request, "vivienda/vacations.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def new_vacation(request):
    """
    Displays new UserIsOut form. If it receives a post request, checks
    that it's valid, and creates a new UserIsOut instance if the POST
    is indeed valid. Otherwise, redirects to the same page and shows an error
    message.
    """
    if request.POST:
        start_date = request.POST.get("fecha_inicio", None)
        end_date = request.POST.get("fecha_fin", None)
        kwargs = {}
        bad_format_error = False
        if start_date is not None:
            try:
                parsed_start_date = datetime.strptime(
                    start_date,
                    settings.DATE_FORMAT).date()
                kwargs['start_date'] = parsed_start_date
            except ValueError:
                bad_format_error = True

        if end_date is not None:
            try:
                parsed_end_date = datetime.strptime(
                    end_date,
                    settings.DATE_FORMAT).date()
                kwargs['end_date'] = parsed_end_date
            except ValueError:
                bad_format_error = True

        if bad_format_error:
            # at least one of the given date strings has an invalid
            # date format
            messages.error(
                request,
                "Las fechas ingresadas no son válidas.")
            return redirect("new_vacation")

        vacation, msg = request.user.go_on_vacation(**kwargs)
        if not vacation:
            messages.error(request, msg)
            return redirect("new_vacation")
        else:
            messages.success(request, msg)
            return redirect("vacations")
    form = UserIsOutForm()
    return render(request, "vivienda/nueva_vacacion.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def edit_vacation(request, vacation_id):
    vacation = get_object_or_404(
        UserIsOut,
        id=vacation_id,
        vivienda_usuario__user=request.user)
    if request.POST:
        start_date = request.POST.get("fecha_inicio", None)
        end_date = request.POST.get("fecha_fin", None)
        kwargs = {}
        bad_format_error = False
        if start_date is not None:
            parsed_start_date = datetime.strptime(
                start_date, settings.DATE_FORMAT).date()
            bad_format_error = bad_format_error or parsed_start_date is None
            kwargs['start_date'] = parsed_start_date
        if end_date is not None:
            parsed_end_date = datetime.strptime(
                end_date, settings.DATE_FORMAT).date()
            bad_format_error = bad_format_error or parsed_end_date is None
            kwargs['end_date'] = parsed_end_date

        if bad_format_error:
            # at least one of the given date strings has an invalid
            # date format
            messages.error(
                request,
                "Las fechas ingresadas no son válidas.")
            return redirect("edit_vacation", vacation_id=int(vacation_id))

        # edit vacation
        edited_vacation, msg = request.user.update_vacation(vacation, **kwargs)
        if not edited_vacation:
            messages.error(request, msg)
            return redirect("edit_vacation", vacation_id=int(vacation_id))
        else:
            messages.success(request, msg)
            return redirect("vacations")

    form = UserIsOutForm(request.POST or None, instance=vacation)
    return render(request, "vivienda/editar_vacacion.html", locals())
