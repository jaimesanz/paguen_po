# -*- coding: utf-8 -*-
from django.contrib import admin

from households.models import Vivienda, ViviendaUsuario, Invitacion

admin.site.register(Vivienda)
admin.site.register(ViviendaUsuario)
admin.site.register(Invitacion)
