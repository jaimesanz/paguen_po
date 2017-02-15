# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views

urlpatterns = [

    # viviendas
    url(r'^vivienda/$', views.vivienda, name='vivienda'),
    url(r'^nueva_vivienda/$', views.nueva_vivienda, name='nueva_vivienda'),
    url(r'^user_info/$', views.user_info, name='user_info'),
    url(r'^manage_users/$', views.manage_users, name='manage_users'),
    url(r'^abandon/$', views.abandon, name='abandon'),
    url(r'^vivienda/balance/$', views.balance, name='balance'),
    url(r'^transfer/$', views.transfer, name='transfer'),

    # invites
    url(r'^invites_list/$', views.invites_list, name='invites_list'),
    url(r'^invite_user/$', views.invite_user, name='invite_user'),
    url(r'^invite/(?P<invite_id>.*)/$', views.invite, name='invite')

]
