# -*- coding: utf-8 -*-
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from core.custom_decorators import request_passes_test
from core.utils import user_has_vivienda
from categories.models import Categoria
from periods.models import get_current_year_month_obj, YearMonth
from .models import Presupuesto
from .forms import PresupuestoForm, PresupuestoEditForm


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def presupuestos(request):
    this_year_month = get_current_year_month_obj()
    return redirect("presupuestos_period", this_year_month.year, this_year_month.month)


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def presupuestos_period(request, year, month):
    vivienda_usuario = request.user.get_vu()
    this_period = get_object_or_404(
        YearMonth,
        year=year,
        month=month)
    presupuestos = Presupuesto.objects.filter(
        vivienda=request.user.get_vivienda(),
        year_month=this_period.id)
    next_year, next_month = this_period.get_next_period()
    prev_year, prev_month = this_period.get_prev_period()
    return render(request, "vivienda/presupuestos.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def nuevo_presupuesto(request):
    vivienda_usuario = request.user.get_vu()
    if request.POST:
        categoria_id = request.POST.get("categoria", None)
        if categoria_id is None:
            messages.error(request, 'Debe ingresar una categoría')
        period = request.POST.get("year_month", None)
        if period is None:
            messages.error(request, 'Debe ingresar un período')
        monto = request.POST.get("monto", None)
        if monto is None or int(monto) <= 0:
            messages.error(request, 'Debe ingresar un monto superior a 0')
        if any(val is None for val in [categoria_id,
                                       period,
                                       monto]):
            return redirect("nuevo_presupuesto")

        year_month = YearMonth.objects.get(
            id=request.POST.get("year_month", None))
        vivienda = vivienda_usuario.vivienda
        categoria = Categoria.objects.get(id=categoria_id)

        presupuesto, created = Presupuesto.objects.get_or_create(
            vivienda=vivienda,
            categoria=categoria,
            year_month=year_month)
        if not created:
            messages.error(request,
                           """
                Ya existe un presupuesto para el período seleccionado
                """)
            return redirect("nuevo_presupuesto")
        presupuesto.monto = monto
        presupuesto.save()
        messages.success(request,
                         """
                        El presupuesto fue creado exitósamente
                        """)
        return redirect(
            "presupuestos_period",
            year_month.year,
            year_month.month)
    form = PresupuestoForm()
    form.fields[
        "categoria"].queryset = vivienda_usuario.vivienda.get_categorias()
    return render(request, "vivienda/nuevo_presupuesto.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def graphs_presupuestos(request):
    this_year_month = get_current_year_month_obj()
    return redirect("graphs_presupuestos_period", this_year_month.year, this_year_month.month)


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def graphs_presupuestos_period(request, year, month):
    this_period = get_object_or_404(
        YearMonth,
        year=year,
        month=month)
    presupuestos = Presupuesto.objects.filter(
        vivienda=request.user.get_vivienda(),
        year_month=this_period.id)
    next_year, next_month = this_period.get_next_period()
    prev_year, prev_month = this_period.get_prev_period()
    return render(request, "vivienda/graphs/presupuestos.html", locals())


@login_required
@request_passes_test(user_has_vivienda,
                     login_url="error",
                     redirect_field_name=None)
def edit_presupuesto(request, year, month, categoria):
    vivienda = request.user.get_vivienda()
    categoria = get_object_or_404(
        Categoria,
        nombre=categoria,
        vivienda=vivienda)
    year_month = get_object_or_404(YearMonth, year=year, month=month)
    presupuesto = get_object_or_404(
        Presupuesto,
        year_month=year_month,
        categoria=categoria,
        vivienda=vivienda)
    if request.POST:
        def redirect_to_invalid_monto():
            messages.error(request, "Debe ingresar un monto mayor a 0")
            return redirect(
                "edit_presupuesto",
                int(year),
                int(month),
                categoria)

        form = PresupuestoEditForm(request.POST)
        if form.is_valid():
            nuevo_monto = request.POST.get("monto", None)
            try:
                nuevo_monto = int(nuevo_monto)
                if nuevo_monto <= 0:
                    return redirect_to_invalid_monto()
            except ValueError:
                return redirect_to_invalid_monto()

            presupuesto.monto = nuevo_monto
            presupuesto.save()
            messages.success(request, "Presupuesto modificado con éxito")
            return redirect(
                "graphs_presupuestos_period",
                year_month.year,
                year_month.month)
        else:
            return redirect_to_invalid_monto()

    form = PresupuestoEditForm(initial=presupuesto.__dict__)
    return render(request, "vivienda/edit_presupuesto.html", locals())


@login_required
def get_old_presupuesto(request):
    ans = []
    categoria = request.POST.get("categoria", None)
    year_month = request.POST.get("year_month", None)
    if categoria is not None and year_month is not None:
        presupuesto = Presupuesto.objects.filter(
            categoria=categoria,
            year_month=year_month,
            vivienda=request.user.get_vivienda()).first()
        if presupuesto is not None:
            ans.append((
                presupuesto.categoria.nombre,
                presupuesto.year_month.id,
                presupuesto.monto))
    return HttpResponse(json.dumps(ans))
