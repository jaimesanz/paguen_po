# -*- coding: utf-8 -*-
from django import forms

from .models import Vivienda, Invitacion


class ViviendaForm(forms.ModelForm):

    class Meta:
        model = Vivienda
        fields = ('alias',)


class InvitacionForm(forms.ModelForm):

    class Meta:
        model = Invitacion
        fields = ("email",)