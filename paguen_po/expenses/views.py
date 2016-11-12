import json
from datetime import datetime

import xlwt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.utils import timezone

from expenses.models import Gasto, ConfirmacionGasto
from expenses_manager.custom_decorators import request_passes_test
from expenses_manager.forms import GastoForm, EditGastoForm
from expenses_manager.utils import user_has_vivienda, write_gastos_to_xls_sheet, \
    get_periods
from periods.models import YearMonth, get_current_year_month_obj


@login_required(redirect_field_name='gastos')
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def get_gastos_xls(request):
    # compute gastos
    vu = request.user.get_vu()
    gastos_pendientes, gastos_pagados = vu.get_gastos_vivienda()
    gastos_pendientes_confirmacion = \
        vu.vivienda.get_pending_confirmation_gastos()

    # create XLS file
    wb = xlwt.Workbook()
    # create each worksheet and write to them
    write_gastos_to_xls_sheet(
        wb.add_sheet('Gastos Pagados'),
        gastos_pagados)
    write_gastos_to_xls_sheet(
        wb.add_sheet('Gastos Pendientes Confirmación'),
        gastos_pendientes_confirmacion)
    write_gastos_to_xls_sheet(
        wb.add_sheet('Gastos Pendientes'),
        gastos_pendientes)

    # create response object with said file
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=gastos.xls'
    wb.save(response)
    return response


@login_required
def get_gastos_graph(request):
    """
    Receives a POST of the form:
    {
        periods : "['2016-4', ..., '2017-2']",
        categorias : "['cat1', 'cat2', ...]",
        include_total : 0 (or 1)
    }
    Note that the values of the keys are STRNGS, not lists.

    Returns a dict of the form {String : [int, ...] , ...} where
    the string represents the name of the categoría, and the array of Integers
    represents the total amount of expenses for that categoria in that period
    of time (The index of the value represents the period of time)
    """

    periods_json = request.POST.get("periods", None)
    categorias_json = request.POST.get("categorias", None)
    if periods_json is None or categorias_json is None:
        return HttpResponse(json.dumps({}))
    periods = json.loads(periods_json)
    categorias = json.loads(categorias_json)
    vivienda = request.user.get_vivienda()
    year_months = [YearMonth.objects.get(
        year=p.split("-")[0], month=p.split("-")[1]) for p in periods]

    res = {}
    # total values
    if (request.POST.get("include_total", None) and
            int(request.POST.get("include_total", None)) > 0):
        total_values = []
        for ym in year_months:
            total_values.append(vivienda.get_total_expenses_period(ym))
        res["total"] = total_values

    # values per categoria
    for c in categorias:
        values = []
        for ym in year_months:
            values.append(
                vivienda.get_total_expenses_categoria_period(
                    c,
                    ym))
        res[c] = values
    return HttpResponse(json.dumps(res))


@login_required
def nuevo_gasto(request):
    vivienda_usuario = request.user.get_vu()
    if request.POST:
        form = GastoForm(request.POST, request.FILES)
        if form.is_valid():
            # if fecha_pago is a future one, don't create Gasto and inform
            kwargs = {}
            fecha_pago_raw = request.POST.get("fecha_pago", None)
            if fecha_pago_raw is not None:
                try:
                    fecha_pago = datetime.strptime(
                        fecha_pago_raw,
                        settings.DATE_FORMAT).date()
                    if fecha_pago <= timezone.now().date():
                        kwargs["fecha_pago"] = fecha_pago
                    else:
                        messages.error(
                            request,
                            "No puede crear un Gasto para una fecha futura.")
                        return redirect("gastos")
                except ValueError:
                    # can't parse date, invalid format!
                    pass
            # set the user who created this
            nuevo_gasto = form.save(commit=False)
            nuevo_gasto.creado_por = request.user.get_vu()
            messages.success(
                request,
                "El gasto fue creado exitósamente")
            # check if it's paid
            is_paid = request.POST.get("is_paid", None)
            if is_paid == "yes":
                nuevo_gasto.pay(request.user.get_vu(), **kwargs)
            nuevo_gasto.save()
            return redirect("gastos")
        # form is not valid or missing/invalid "is_paid" field
        messages.error(request, "El formulario contiene errores")
        return redirect("gastos")
    return redirect("gastos")


@login_required
def gastos(request):
    vu = request.user.get_vu()
    if vu is None:
        return redirect("error")
    # get list of gastos
    gastos_pendientes_list, gastos_pagados_list = vu.get_gastos_vivienda()
    gastos_pendientes_confirmacion_list = \
        vu.vivienda.get_pending_confirmation_gastos()
    gasto_form = GastoForm()
    gasto_form.fields["categoria"].queryset = vu.vivienda.get_categorias()
    today = timezone.now().date().strftime(settings.DATE_FORMAT)
    gasto_form.fields["fecha_pago"].initial = today
    return render(request, "gastos/gastos.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def graph_gastos(request):
    vivienda = request.user.get_vivienda()
    today = timezone.now()
    current_year_month = get_current_year_month_obj()
    total_this_period = vivienda.get_total_expenses_period(current_year_month)
    categorias = vivienda.get_categorias()
    categoria_total = []
    for c in categorias:
        categoria_total.append((
            c,
            vivienda.get_total_expenses_categoria_period(
                c,
                current_year_month)))
    # TODO this window defines how far in the past the user can graph
    # it's set to 12 months, but in the future must be customizable
    # by the user. Also, the window should be measured in months
    window = 1  # year
    periods = ["%d-%d" % (y, m) for y, m in get_periods(
        today.year - window,
        today.month,
        today.year,
        today.month)]

    return render(
        request,
        "vivienda/graphs/gastos.html",
        {
            "periods": json.dumps(periods),
            "periods_indexes": json.dumps(
                [i for i in range(1, len(periods) + 1)]),
            "periods_indexes_max": len(periods),
            "vivienda": vivienda,
            "today": today,
            "current_year_month": current_year_month,
            "total_this_period": total_this_period,
            "categorias": categorias,
            "categoria_total": categoria_total,
            "window": window
        })


@login_required
def detalle_gasto(request, gasto_id):
    vivienda_usuario = request.user.get_vu()
    gasto = get_object_or_404(Gasto, id=gasto_id)
    if not gasto.allow_user(request.user):
        messages.error(
            request,
            "Usted no está autorizado para ver esta página")
        return redirect("error")
    gasto_form = GastoForm(model_to_dict(gasto))
    if request.POST:
        if gasto.is_paid() or gasto.is_pending_confirm():
            messages.error(
                request,
                "El gasto ya se encuentra pagado.")
            return redirect("error")
        messages.success(
            request,
            "El gasto fue pagado con éxito")
        gasto.pay(request.user.get_vu())
        return redirect("detalle_gasto", gasto.id)

    show_confirm_form = False
    if gasto.is_pending_confirm():
        # if it's confirmed, don't show the "confirm" button. Likewise,
        # if it's not confirmed, show the button
        show_confirm_form = not ConfirmacionGasto.objects.get(
            vivienda_usuario=request.user.get_vu(),
            gasto=gasto
        ).confirmed

    allowed_user = gasto.is_pending() or gasto.usuario == request.user.get_vu()
    show_edit_button = allowed_user and not gasto.categoria.is_transfer

    return render(request, "gastos/detalle_gasto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def edit_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id)
    if not gasto.allow_user(request.user):
        messages.error(
            request,
            "Usted no está autorizado para ver esta página.")
        return redirect("error")

    if gasto.categoria.is_transfer:
        messages.error(
            request,
            "Usted no está autorizado para ver esta página.")
        return redirect("detalle_gasto", gasto.id)

    if request.POST:
        new_monto = request.POST.get("monto", None)
        new_fecha = request.POST.get("fecha_pago", None)
        parsed_new_fecha = None
        parsed_new_monto = None
        # validate new_fecha
        try:
            parsed_new_fecha = datetime.strptime(
                new_fecha,
                settings.DATE_FORMAT).date()
            if parsed_new_fecha > timezone.now().date():
                messages.error(
                    request,
                    "No puede crear un Gasto para una fecha futura."
                )
                return redirect("edit_gasto", gasto.id)
        except ValueError:
            messages.error(
                request,
                "La fecha ingresada no es válida."
            )
            return redirect("edit_gasto", gasto.id)
        # validate new_monto
        try:
            parsed_new_monto = int(new_monto)
        except ValueError:
            pass
        if parsed_new_monto is None or parsed_new_monto <= 0:
            messages.error(
                request,
                "El monto ingresado debe ser un número mayor que 0."
            )
            return redirect("edit_gasto", gasto.id)

        msg = gasto.edit(request.user.get_vu(), new_monto, parsed_new_fecha)
        if msg == "No tiene permiso para editar este Gasto":
            messages.error(request, msg)
        else:
            messages.success(request, msg)
        return redirect("detalle_gasto", gasto.id)

    show_delete_button = gasto.is_pending() or \
        gasto.usuario == request.user.get_vu()

    if not show_delete_button:
        messages.error(
            request,
            "Usted no está autorizado para ver esta página."
        )
        return redirect("detalle_gasto", gasto.id)

    form = EditGastoForm(request.POST or None, instance=gasto)
    return render(request, "gastos/edit_gasto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def confirm_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, id=gasto_id)
    if not gasto.allow_user(request.user):
        messages.error(
            request,
            "Usted no está autorizado para ver esta página")
        return redirect("error")
    if request.POST:
        vu = request.user.get_vu()
        if ConfirmacionGasto.objects.get(
                gasto=gasto,
                vivienda_usuario=vu).confirmed:
            messages.error(request, "Usted ya confirmó este Gasto")
        else:
            vu.confirm(gasto)
            if gasto.is_paid():
                # this means everyone confirmed
                messages.success(
                    request,
                    "El gasto fue confirmado por todos los usuarios "
                    "pertinentes.")
            else:
                messages.success(
                    request,
                    "Gasto confirmado.")

    return redirect("detalle_gasto", gasto.id)


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def delete_gasto(request):
    if request.POST:
        gasto_id = request.POST.get("gasto", None)
        if gasto_id is not None:
            gasto = get_object_or_404(Gasto, id=gasto_id)
            if gasto.is_pending() or gasto.usuario == request.user.get_vu():
                messages.success(request, "Gasto eliminado.")
                gasto.delete()
            else:
                messages.error(
                    request,
                    "No tiene permiso para eliminar este Gasto")
                return redirect("detalle_gasto", gasto.id)

    # do nothing
    return redirect("gastos")