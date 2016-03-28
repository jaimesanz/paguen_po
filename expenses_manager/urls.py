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
	url(r'^consultar_vivienda/$', views.consultar_vivienda, name='consultar_vivienda'),
	url(r'^user_info/$', views.user_info, name='user_info'),
	url(r'^login_post_process/$', views.login_post_process, name='login_post_process'),
	url(r'^$', views.home, name='home')
]