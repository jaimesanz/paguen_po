# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings

from .models import Gasto


class GastoForm(forms.ModelForm):

    fecha_pago = forms.DateInput(format=settings.DATE_FORMAT)

    class Meta:
        model = Gasto
        fields = ('categoria', 'monto', 'foto', 'fecha_pago')


class EditGastoForm(forms.ModelForm):

    class Meta:
        model = Gasto
        fields = ('monto', 'fecha_pago')
        widgets = {
            'fecha_pago': forms.DateInput(format=settings.DATE_FORMAT)
        }