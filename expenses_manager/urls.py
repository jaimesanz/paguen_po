# -*- coding: utf-8 -*-
import expenses_manager.file_dispatchers
from django.conf.urls import include, url
from django.contrib import admin
from registration.forms import RegistrationFormUniqueEmail
from registration.backends.hmac.views import RegistrationView
from django.conf import settings
from django.conf.urls.static import static
from . import views
from . import ajax_dispatchers


class RegistrationViewUniqueEmail(RegistrationView):
    """
    Override default django-registration "register" view so that it enforces a
    unique email in the registration-form
    """
    form_class = RegistrationFormUniqueEmail

urlpatterns = [
    # django admin page
    url(r'^admin/', admin.site.urls),

    # display info
    url(r'^home/', views.home, name='home'),
    url(r'^about/$', views.about, name='about'),
    url(r'^error/$', views.error, name='error'),

    # registration
    url(r'^accounts/register/$', RegistrationViewUniqueEmail.as_view(),
        name='registration_register'),
    url(r'^accounts/', include('registration.backends.hmac.urls')),
    url(r'^login_post_process/$', views.login_post_process,
        name='login_post_process'),

    # vivienda
    url(r'^vivienda/$', views.vivienda, name='vivienda'),
    url(r'^nueva_vivienda/$', views.nueva_vivienda, name='nueva_vivienda'),
    url(r'^user_info/$', views.user_info, name='user_info'),
    url(r'^manage_users/$', views.manage_users, name='manage_users'),
    url(r'^abandon/$', views.abandon, name='abandon'),
    url(r'^vivienda/balance/$', views.balance, name='balance'),
    url(r'^transfer/$', views.transfer, name='transfer'),

    # vacations
    url(r'^vivienda/vacaciones/$', views.vacations, name='vacations'),
    url(r'^vivienda/vacaciones/new/$',
        views.new_vacation,
        name='new_vacation'),
    url(r'^vivienda/vacaciones/(?P<vacation_id>\d+)/$',
        views.edit_vacation,
        name='edit_vacation'),

    # invites
    url(r'^invites_list/$', views.invites_list, name='invites_list'),
    url(r'^invite_user/$', views.invite_user, name='invite_user'),
    url(r'^invite/(?P<invite_id>.*)/$', views.invite, name='invite'),

    # categorías
    url(r'^vivienda/categorias/$', views.categorias, name='categorias'),
    url(r'^vivienda/categorias/new/$',
        views.nueva_categoria,
        name='nueva_categoria'),
    url(r'^vivienda/categorias/delete/$',
        views.delete_categoria,
        name='delete_categoria'),
    url(r'^vivienda/categoria/(\d+)/$', views.edit_categoria,
        name='edit_categoria'),

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

    # presupuestos
    url(r'^presupuestos/$', views.presupuestos, name='presupuestos'),
    url(r'^presupuestos/(\d+)/(\d+)/(.+)/$',
        views.edit_presupuesto,
        name='edit_presupuesto'),
    url(r'^presupuestos/(\d+)/(\d+)$',
        views.presupuestos_period,
        name='presupuestos_period'),
    url(r'^graphs/presupuestos/$',
        views.graphs_presupuestos,
        name='graphs_presupuestos'),
    url(r'^graphs/presupuestos/(\d+)/(\d+)$',
        views.graphs_presupuestos_period, name='graphs_presupuestos_period'),
    url(r'^presupuestos/new/$',
        views.nuevo_presupuesto,
        name='nuevo_presupuesto'),

    # AJAX urls
    url(r'^get_items_autocomplete/$', ajax_dispatchers.get_items_autocomplete,
        name='get_items_autocomplete'),
    url(r'^get_old_presupuesto/$', ajax_dispatchers.get_old_presupuesto,
        name='get_old_presupuesto'),
    url(r'^get_gastos_graph/$', ajax_dispatchers.get_gastos_graph,
        name='get_gastos_graph'),

    # file download urls
    url(r'^get_gastos_xls/$', expenses_manager.file_dispatchers.get_gastos_xls,
        name='get_gastos_xls'),

    # default to home
    url(r'^$', views.home, name='home')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
