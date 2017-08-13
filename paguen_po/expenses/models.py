# -*- coding: utf-8 -*-
from django.db import models
from model_utils.models import StatusModel
from model_utils import Choices


class Category(models.Model):
    """A category for a given Expense."""
    name = models.CharField("nombre", unique=True, max_length=128)


class Expense(StatusModel):
    """An expense a user made for a given Household."""
    STATUS = Choices('pendiente', 'pagado')

    amount = models.PositiveIntegerField("monto")
    category = models.ForeignKey("expenses.Category", null=True)
    user = models.ForeignKey("auth.User", null=True)
    year = models.PositiveIntegerField("año")
    month = models.PositiveIntegerField("mes")
