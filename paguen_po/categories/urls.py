# -*- coding: utf-8 -*-
from django.conf.urls import url

from categories import views

urlpatterns = [

    url(r'^vivienda/categorias/$', views.categorias, name='categorias'),
    url(r'^vivienda/categorias/new/$',
        views.nueva_categoria,
        name='nueva_categoria'),
    url(r'^vivienda/categorias/delete/$',
        views.delete_categoria,
        name='delete_categoria'),
    url(r'^vivienda/categoria/(\d+)/$', views.edit_categoria,
        name='edit_categoria')

]
