# -*- coding: utf-8 -*-
"""project_root URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

from core import views

urlpatterns = [

    # django admin page
    url(r'^admin/', admin.site.urls),

    # display info
    url(r'^home/', views.home, name='home'),
    url(r'^about/$', views.about, name='about'),
    url(r'^error/$', views.error, name='error'),

    # registration
    url(r'', include('users.urls')),

    # viviendas and invites
    url(r'', include('households.urls')),

    # vacations
    url(r'', include('vacations.urls')),

    # categorías
    url(r'', include('categories.urls')),

    # presupuestos
    url(r'', include('budgets.urls')),

    # listas and items
    url(r'', include('groceries.urls')),

    # gastos
    url(r'', include('expenses.urls')),

    # default to home
    url(r'', views.home, name='home'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)