# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views

urlpatterns = [

    url(r'^get_user_data$', views.get_user_data, name="get_user_data"),
    url(r'^$', views.index, name="index")

]
