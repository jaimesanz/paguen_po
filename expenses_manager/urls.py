# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin

from . import views

urlpatterns = [
	url(r'^admin/', admin.site.urls),
	url(r'^home/', views.home, name='home'),
	url(r'^accounts/', include('registration.backends.hmac.urls')),
	url(r'^login_test/$', views.login_test, name='login_test'),
	url(r'^invites_list/$', views.invites_list, name='invites_list'),
	url(r'^nueva_vivienda/$', views.nueva_vivienda, name='nueva_vivienda'),
	url(r'^$', views.home, name='home')
]