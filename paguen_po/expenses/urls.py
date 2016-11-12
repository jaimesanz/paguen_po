# -*- coding: utf-8 -*-
from django.conf.urls import url

from expenses import views

urlpatterns = [
    url(r'^gastos/$', views.gastos, name='gastos'),
    url(r'^nuevo_gasto/$', views.nuevo_gasto, name='nuevo_gasto'),
    url(r'^detalle_gasto/(?P<gasto_id>.*)/$',
        views.detalle_gasto, name='detalle_gasto'),
    url(r'^edit_gasto/(\d+)/$',
        views.edit_gasto, name='edit_gasto'),
    url(r'^graphs/gastos/$', views.graph_gastos, name='graph_gastos'),
    url(r'^confirm/(\d+)/$',
        views.confirm_gasto,
        name='confirm_gasto'),
    url(r'^gastos/delete/$', views.delete_gasto, name='delete_gasto'),

    # file download urls
    url(r'^get_gastos_xls/$', views.get_gastos_xls,
        name='get_gastos_xls'),

    url(r'^get_gastos_graph/$', views.get_gastos_graph,
        name='get_gastos_graph')
]
