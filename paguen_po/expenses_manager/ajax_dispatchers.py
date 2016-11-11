# -*- coding: utf-8 -*-
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import *


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
def get_items_autocomplete(request):
    if 'term' in request.GET:
        items = Item.objects.filter(
            vivienda=request.user.get_vivienda(),
            nombre__istartswith=request.GET['term'])
        return HttpResponse(
            json.dumps(
                [(item.nombre, item.unidad_medida) for item in items]))


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
