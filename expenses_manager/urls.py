# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin

from . import views

urlpatterns = [
    # django admin page
    url(r'^admin/', admin.site.urls),

    # display info
    url(r'^home/', views.home, name='home'),
    url(r'^about/$', views.about, name='about'),
    url(r'^error/$', views.error, name='error'),

    # registration
    url(r'^accounts/', include('registration.backends.hmac.urls')),
    url(r'^login_post_process/$', views.login_post_process,
        name='login_post_process'),
    
    # vivienda
    url(r'^vivienda/$', views.vivienda, name='vivienda'),
    url(r'^nueva_vivienda/$', views.nueva_vivienda, name='nueva_vivienda'),
    url(r'^user_info/$', views.user_info, name='user_info'),
    url(r'^manage_users/$', views.manage_users, name='manage_users'),
    url(r'^abandon/$', views.abandon, name='abandon'),

    # invites
    url(r'^invites_list/$', views.invites_list, name='invites_list'),
    url(r'^invite_user/$', views.invite_user, name='invite_user'),
    url(r'^invite/(?P<invite_id>.*)/$', views.invite, name='invite'),

    # gastos
    url(r'^gastos/$', views.gastos, name='gastos'),
    url(r'^nuevo_gasto/$', views.nuevo_gasto, name='nuevo_gasto'),
    url(r'^detalle_gasto/(?P<gasto_id>.*)/$',
        views.detalle_gasto, name='detalle_gasto'),
    url(r'^graphs/gastos/$', views.graph_gastos, name='graph_gastos'),

    # listas
    url(r'^nueva_lista/$', views.nueva_lista, name='nueva_lista'),
    url(r'^lists/$', views.lists, name='lists'),
    url(r'^detalle_lista/(?P<lista_id>.*)/$',
        views.detalle_lista, name='detalle_lista'),
    
    # presupuestos
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

    # AJAX urls
    url(r'^get_items_autocomplete/$', views.get_items_autocomplete,
        name='get_items_autocomplete'),
    url(r'^get_old_presupuesto/$', views.get_old_presupuesto,
        name='get_old_presupuesto'),
    url(r'^get_gastos_graph/$', views.get_gastos_graph,
        name='get_gastos_graph'),
    

    # default to home
    url(r'^$', views.home, name='home')
]
