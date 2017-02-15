# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User

from .models import Vivienda, Invitacion


class ViviendaForm(forms.ModelForm):

    class Meta:
        model = Vivienda
        fields = ('alias',)


class InvitacionForm(forms.ModelForm):

    class Meta:
        model = Invitacion
        fields = ("email",)


class TransferForm(forms.Form):
    monto = forms.IntegerField(label='Monto')
    user = forms.ModelChoiceField(
        label="Usuario",
        queryset=User.objects.none())
