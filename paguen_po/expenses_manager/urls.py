# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static

from registration.forms import RegistrationFormUniqueEmail
from registration.backends.hmac.views import RegistrationView

from . import views
from . import ajax_dispatchers


class RegistrationViewUniqueEmail(RegistrationView):
    """Override default django-registration "register" view so that it
    enforces a unique email in the registration-form.
    """
    form_class = RegistrationFormUniqueEmail

urlpatterns = [

    # registration
    url(r'^accounts/register/$', RegistrationViewUniqueEmail.as_view(),
        name='registration_register'),
    url(r'^accounts/', include('registration.backends.hmac.urls')),
    url(r'^login_post_process/$', views.login_post_process,
        name='login_post_process'),

    # AJAX urls
    url(r'^get_items_autocomplete/$', ajax_dispatchers.get_items_autocomplete,
        name='get_items_autocomplete'),
    url(r'^get_old_presupuesto/$', ajax_dispatchers.get_old_presupuesto,
        name='get_old_presupuesto'),

    # default to home
    url(r'^$', views.home, name='home')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
