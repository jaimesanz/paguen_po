# -*- coding: utf-8 -*-
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from budgets.models import Presupuesto
from groceries.models import Item


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
