# -*- coding: utf-8 -*-
from django.db import models
from model_utils.models import StatusModel
from model_utils import Choices


class Category(models.Model):
    """A category for a given Expense."""
    name = models.CharField("nombre", unique=True, max_length=128)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return "{}".format(self.name)


class Expense(StatusModel):
    """An expense a user made for a given Household."""
    STATUS = Choices(
        ('PENDING', 'pendiente'),
        ('PAID', 'pagado')
    )

    amount = models.PositiveIntegerField("monto")
    category = models.ForeignKey("expenses.Category", null=True)
    roommate = models.ForeignKey("households.Roommate", on_delete=models.CASCADE)
    year = models.PositiveIntegerField("año")
    month = models.PositiveIntegerField("mes")
