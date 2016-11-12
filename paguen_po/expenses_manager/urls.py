# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static

from registration.forms import RegistrationFormUniqueEmail
from registration.backends.hmac.views import RegistrationView

from . import file_dispatchers
from . import views
from . import ajax_dispatchers


class RegistrationViewUniqueEmail(RegistrationView):
    """
    Override default django-registration "register" view so that it enforces a
    unique email in the registration-form
    """
    form_class = RegistrationFormUniqueEmail

urlpatterns = [

    # registration
    url(r'^accounts/register/$', RegistrationViewUniqueEmail.as_view(),
        name='registration_register'),
    url(r'^accounts/', include('registration.backends.hmac.urls')),
    url(r'^login_post_process/$', views.login_post_process,
        name='login_post_process'),

    # items
    url(r'^vivienda/items/$', views.items, name='items'),
    url(r'^vivienda/items/new/$', views.new_item, name='new_item'),
    url(r'^vivienda/item/(.+)/$', views.edit_item, name='edit_item'),

    # gastos
    url(r'^gastos/$', views.gastos, name='gastos'),
    url(r'^nuevo_gasto/$', views.nuevo_gasto, name='nuevo_gasto'),
    url(r'^detalle_gasto/(?P<gasto_id>.*)/$',
        views.detalle_gasto, name='detalle_gasto'),
    url(r'^edit_gasto/(\d+)/$',
        views.edit_gasto, name='edit_gasto'),
    url(r'^graphs/gastos/$', views.graph_gastos, name='graph_gastos'),
    url(r'^confirm/(\d+)/$',
        views.confirm_gasto,
        name='confirm_gasto'),
    url(r'^gastos/delete/$', views.delete_gasto, name='delete_gasto'),

    # listas
    url(r'^nueva_lista/$', views.nueva_lista, name='nueva_lista'),
    url(r'^lists/new/$', views.lists, name='lists'),
    url(r'^detalle_lista/(?P<lista_id>.*)/$',
        views.detalle_lista, name='detalle_lista'),
    url(r'^edit_list/(?P<lista_id>.*)/$', views.edit_list,
        name='edit_list'),


    # AJAX urls
    url(r'^get_items_autocomplete/$', ajax_dispatchers.get_items_autocomplete,
        name='get_items_autocomplete'),
    url(r'^get_old_presupuesto/$', ajax_dispatchers.get_old_presupuesto,
        name='get_old_presupuesto'),
    url(r'^get_gastos_graph/$', ajax_dispatchers.get_gastos_graph,
        name='get_gastos_graph'),

    # file download urls
    url(r'^get_gastos_xls/$', file_dispatchers.get_gastos_xls,
        name='get_gastos_xls'),

    # default to home
    url(r'^$', views.home, name='home')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
