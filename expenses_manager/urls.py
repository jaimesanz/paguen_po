from django.conf.urls import url
from django.contrib import admin

from . import views

urlpatterns = [
	url(r'^admin/', admin.site.urls),
    url(r'^manage/', views.index, name='index'),
    url(r'', views.index, name='index')
]