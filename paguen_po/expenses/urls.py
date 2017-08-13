# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views

urlpatterns = [

    url(r'^categories/$', views.CategoryList.as_view(), name="index")

]
