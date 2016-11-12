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
from django.conf.urls import include, url
from django.contrib import admin

from expenses_manager import views

urlpatterns = [

    # django admin page
    url(r'^admin/', admin.site.urls),

    # display info
    url(r'^home/', views.home, name='home'),
    url(r'^about/$', views.about, name='about'),
    url(r'^error/$', views.error, name='error'),

    # viviendas and invites
    url(r'', include('households.urls')),

    # vacations
    url(r'', include('vacations.urls')),

    url(r'', include('expenses_manager.urls'))
]
