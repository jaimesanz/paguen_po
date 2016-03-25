# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Vivienda)
admin.site.register(ViviendaUsuario)
admin.site.register(Invitacion)
admin.site.register(SolicitudAbandonarVivienda)
admin.site.register(Categoria)