# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^vivienda/vacaciones/$', views.vacations, name='vacations'),
    url(r'^vivienda/vacaciones/new/$',
        views.new_vacation,
        name='new_vacation'),
    url(r'^vivienda/vacaciones/(?P<vacation_id>\d+)/$',
        views.edit_vacation,
        name='edit_vacation')

]
