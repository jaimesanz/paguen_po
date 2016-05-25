# -*- coding: utf-8 -*-
from django import forms
from .models import *
from django.contrib.auth.models import User
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


class TransferForm(forms.Form):
    monto = forms.IntegerField(label='Monto')
    user = forms.ModelChoiceField(
        label="Usuario",
        queryset=User.objects.none())
