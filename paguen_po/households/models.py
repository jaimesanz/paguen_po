# -*- coding: utf-8 -*-
from django.db import models


class Household(models.Model):
    """A Households that contains Users and Expenses."""
    name = models.CharField("alias", max_length=100)
    users = models.ManyToManyField("auth.User")
