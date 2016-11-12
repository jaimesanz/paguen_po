# -*- coding: utf-8 -*-
from django.contrib import admin

from groceries.models import Item, ListaCompras, ItemLista

# Register your models here.
admin.site.register(Item)
admin.site.register(ListaCompras)
admin.site.register(ItemLista)
