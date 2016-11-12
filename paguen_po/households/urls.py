# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^vivienda/$', views.vivienda, name='vivienda'),
    url(r'^nueva_vivienda/$', views.nueva_vivienda, name='nueva_vivienda'),
    url(r'^user_info/$', views.user_info, name='user_info'),
    url(r'^manage_users/$', views.manage_users, name='manage_users'),
    url(r'^abandon/$', views.abandon, name='abandon'),
    url(r'^vivienda/balance/$', views.balance, name='balance'),
    url(r'^transfer/$', views.transfer, name='transfer')

]
