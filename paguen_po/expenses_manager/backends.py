# -*- coding: utf-8 -*-
from django.contrib.auth import backends

from .models import ProxyUser


class ModelBackend(backends.ModelBackend):
    """Extending to provide a proxy for user."""

    def get_user(self, user_id):
        try:
            return ProxyUser.objects.get(pk=user_id)
        except ProxyUser.DoesNotExist:
            return None
