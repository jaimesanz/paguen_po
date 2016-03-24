# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin

from . import views

urlpatterns = [
	url(r'^admin/', admin.site.urls),
	url(r'^home/', views.index, name='index'),
	url(r'^register/', views.register, name='register'),
	url(r'^login/$', views.user_login, name='login'),
	url(r'^login_test/$', views.login_test, name='login_test')
]