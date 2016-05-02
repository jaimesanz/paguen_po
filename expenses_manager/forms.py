# -*- coding: utf-8 -*-
from django import forms
from .models import *
from django.contrib.auth.models import User, Group
from django.conf import settings

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password')


class ViviendaForm(forms.ModelForm):

    class Meta:
        model = Vivienda
        fields = ('alias',)


class InvitacionForm(forms.ModelForm):

    class Meta:
        model = Invitacion
        fields = ("email",)


class GastoForm(forms.ModelForm):

    class Meta:
        model = Gasto
        fields = ('monto', 'categoria')


class PresupuestoForm(forms.ModelForm):

    class Meta:
        model = Presupuesto
        fields = ("categoria", "year_month", "monto")


class PresupuestoEditForm(forms.ModelForm):

    class Meta:
        model = Presupuesto
        fields = ("monto",)


class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = ("nombre",)


class ItemForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = ("nombre", "unidad_medida", "descripcion")


class UserIsOutForm(forms.ModelForm):

    class Meta:
        model = UserIsOut
        fields = ("fecha_inicio", "fecha_fin")
        widgets = {
            'fecha_inicio': forms.DateInput(format=settings.DATE_FORMAT),
            'fecha_fin': forms.DateInput(format=settings.DATE_FORMAT),
        }
