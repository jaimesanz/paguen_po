# -*- coding: utf-8 -*-
from django.conf.urls import url

from groceries import views

urlpatterns = [
    # items
    url(r'^vivienda/items/$', views.items, name='items'),
    url(r'^vivienda/items/new/$', views.new_item, name='new_item'),
    url(r'^vivienda/item/(.+)/$', views.edit_item, name='edit_item'),

    # listas
    url(r'^nueva_lista/$', views.nueva_lista, name='nueva_lista'),
    url(r'^lists/new/$', views.lists, name='lists'),
    url(r'^detalle_lista/(?P<lista_id>.*)/$',
        views.detalle_lista, name='detalle_lista'),
    url(r'^edit_list/(?P<lista_id>.*)/$', views.edit_list,
        name='edit_list'),

    url(r'^get_items_autocomplete/$', views.get_items_autocomplete,
        name='get_items_autocomplete')
]
