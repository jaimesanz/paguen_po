# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^presupuestos/$', views.presupuestos, name='presupuestos'),
    url(r'^presupuestos/(\d+)/(\d+)/(.+)/$',
        views.edit_presupuesto,
        name='edit_presupuesto'),
    url(r'^presupuestos/(\d+)/(\d+)$',
        views.presupuestos_period,
        name='presupuestos_period'),
    url(r'^graphs/presupuestos/$',
        views.graphs_presupuestos,
        name='graphs_presupuestos'),
    url(r'^graphs/presupuestos/(\d+)/(\d+)$',
        views.graphs_presupuestos_period, name='graphs_presupuestos_period'),
    url(r'^presupuestos/new/$',
        views.nuevo_presupuesto,
        name='nuevo_presupuesto'),

    url(r'^get_old_presupuesto/$', views.get_old_presupuesto,
        name='get_old_presupuesto')
]
