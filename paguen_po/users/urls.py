# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from registration.forms import RegistrationFormUniqueEmail
from registration.backends.hmac.views import RegistrationView

from . import views


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
        name='login_post_process')
]
