# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^home/', views.home, name='home'),
    url(r'^accounts/', include('registration.backends.hmac.urls')),
    url(r'^invites_list/$', views.invites_list, name='invites_list'),
    url(r'^nueva_vivienda/$', views.nueva_vivienda, name='nueva_vivienda'),
    url(r'^vivienda/$', views.vivienda, name='vivienda'),
    url(r'^user_info/$', views.user_info, name='user_info'),
    url(r'^login_post_process/$', views.login_post_process,
        name='login_post_process'),
    url(r'^about/$', views.about, name='about'),
    url(r'^invite_user/$', views.invite_user, name='invite_user'),
    url(r'^invite/(?P<invite_id>.*)/$', views.invite, name='invite'),
    url(r'^error/$', views.error, name='error'),
    url(r'^manage_users/$', views.manage_users, name='manage_users'),
    url(r'^balance/$', views.balance, name='balance'),
    url(r'^visualizations/$', views.visualizations, name='visualizations'),
    url(r'^abandon/$', views.abandon, name='abandon'),
    url(r'^gastos/$', views.gastos, name='gastos'),

    url(r'^presupuestos/$', views.presupuestos, name='presupuestos'),
    url(r'^presupuestos/(\d+)/(\d+)$',
        views.presupuestos_period, name='presupuestos_period'),
    url(r'^presupuestos/new/$', views.nuevo_presupuesto, name='nuevo_presupuesto'),

    url(r'^nuevo_gasto/$', views.nuevo_gasto, name='nuevo_gasto'),
    url(r'^nueva_lista/$', views.nueva_lista, name='nueva_lista'),
    url(r'^detalle_gasto/(?P<gasto_id>.*)/$',
        views.detalle_gasto, name='detalle_gasto'),
    url(r'^lists/$', views.lists, name='lists'),
    url(r'^detalle_lista/(?P<lista_id>.*)/$',
        views.detalle_lista, name='detalle_lista'),

    url(r'^get_items_autocomplete/$', views.get_items_autocomplete,
        name='get_items_autocomplete'),

    url(r'^$', views.home, name='home')
]
