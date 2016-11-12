# -*- coding: utf-8 -*-
from django.contrib import admin

from users.models import ProxyUser

admin.site.register(ProxyUser)
