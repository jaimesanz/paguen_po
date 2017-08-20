# -*- coding: utf-8 -*-
from django.conf.urls import url
from expenses import views as expenses_views
from households import views as households_views

app_name = 'api'
urlpatterns = [

    url(r'^gastos/$', expenses_views .ExpensesList.as_view(), name="expenses"),
    url(r'^gastos/categorias/$', expenses_views .CategoryList.as_view(), name="categories"),

    url(r'^viviendas/', households_views.HouseholdList.as_view(), name="households")

]
