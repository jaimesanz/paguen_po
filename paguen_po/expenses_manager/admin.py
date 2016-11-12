# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import ViviendaUsuario, UserIsOut, \
	Invitacion, Categoria, Item, YearMonth, Presupuesto, ListaCompras, \
	ItemLista, EstadoGasto, Gasto
from households.models import Vivienda, ViviendaUsuario
from users.models import ProxyUser

admin.site.register(ProxyUser)
admin.site.register(Vivienda)
admin.site.register(ViviendaUsuario)
admin.site.register(UserIsOut)
admin.site.register(Invitacion)
admin.site.register(Categoria)
admin.site.register(Item)
admin.site.register(YearMonth)
admin.site.register(Presupuesto)
admin.site.register(ListaCompras)
admin.site.register(ItemLista)
admin.site.register(EstadoGasto)
admin.site.register(Gasto)
