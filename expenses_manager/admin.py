# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(ProxyUser)
admin.site.register(Vivienda)
admin.site.register(ViviendaUsuario)
admin.site.register(Invitacion)
admin.site.register(SolicitudAbandonarVivienda)
admin.site.register(Categoria)
admin.site.register(Item)
admin.site.register(YearMonth)
admin.site.register(Presupuesto)
admin.site.register(ListaCompras)
admin.site.register(ItemLista)
admin.site.register(EstadoGasto)
admin.site.register(Gasto)
