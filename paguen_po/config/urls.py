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

from rest_framework.documentation import include_docs_urls

api_urls = [

    url(r'^', include('core.urls', namespace='core')),
    url(r'^expenses/', include('expenses.urls', namespace='expenses')),
    url(r'^households/', include('households.urls', namespace='households')),

]

urlpatterns = [

    url(r'^api/', include(api_urls, namespace='api')),

    # django admin page
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^docs/', include_docs_urls(title='PaguenPo API'))

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
