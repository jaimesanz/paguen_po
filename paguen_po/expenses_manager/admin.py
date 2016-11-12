# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Presupuesto, EstadoGasto, Gasto

admin.site.register(Presupuesto)
admin.site.register(EstadoGasto)
admin.site.register(Gasto)
