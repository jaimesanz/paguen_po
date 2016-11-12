# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Invitacion, Item, YearMonth, Presupuesto, ListaCompras, \
	ItemLista, EstadoGasto, Gasto

admin.site.register(Invitacion)
admin.site.register(Item)
admin.site.register(YearMonth)
admin.site.register(Presupuesto)
admin.site.register(ListaCompras)
admin.site.register(ItemLista)
admin.site.register(EstadoGasto)
admin.site.register(Gasto)
