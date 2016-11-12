# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings

from vacations.models import UserIsOut


class UserIsOutForm(forms.ModelForm):

    class Meta:
        model = UserIsOut
        fields = ("fecha_inicio", "fecha_fin")
        widgets = {
            'fecha_inicio': forms.DateInput(format=settings.DATE_FORMAT),
            'fecha_fin': forms.DateInput(format=settings.DATE_FORMAT),
        }