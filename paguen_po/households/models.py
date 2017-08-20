# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models

from model_utils.models import SoftDeletableModel, TimeStampedModel


class Household(SoftDeletableModel):
    """A Households that contains Users and Expenses."""
    name = models.CharField("alias", max_length=100)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, through="Roommate")

    def __str__(self):
        return "{}".format(self.name)


class Roommate(SoftDeletableModel, TimeStampedModel):
    """A user in a Household."""
    household = models.ForeignKey("Household", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return "{} - {}".format(self.household.name, self.user.username)
