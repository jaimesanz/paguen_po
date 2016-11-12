# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.
from periods.models import get_current_year_month


class Presupuesto(models.Model):

    class Meta:
        unique_together = (('categoria', 'vivienda', 'year_month'),)
    categoria = models.ForeignKey("categories.Categoria", on_delete=models.CASCADE)
    vivienda = models.ForeignKey("households.Vivienda", on_delete=models.CASCADE)
    year_month = models.ForeignKey(
        "periods.YearMonth",
        on_delete=models.CASCADE,
        default=get_current_year_month
    )
    monto = models.IntegerField(default=0)

    def __str__(self):
        return "".join((
            str(self.vivienda),
            "__",
            str(self.categoria),
            "__",
            str(self.year_month)))

    def get_total_expenses(self):
        """
        Returns the sum of all paid Gastos of the Presupuesto's Categoria in
        the Presupuesto's YearMonth for the Presupuesto's Vivienda
        :return: Integer
        """
        return self.vivienda.get_total_expenses_categoria_period(
            self.categoria,
            self.year_month)