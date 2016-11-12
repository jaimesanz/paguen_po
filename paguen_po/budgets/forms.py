# -*- coding: utf-8 -*-
from django import forms

from budgets.models import Presupuesto


class PresupuestoForm(forms.ModelForm):

    class Meta:
        model = Presupuesto
        fields = ("categoria", "year_month", "monto")


class PresupuestoEditForm(forms.ModelForm):

    class Meta:
        model = Presupuesto
        fields = ("monto",)