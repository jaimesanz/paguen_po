# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User
from django.conf import settings

from expenses.models import Gasto
from budgets.models import Presupuesto
from groceries.models import Item, ItemLista
from vacations.models import UserIsOut
from categories.models import Categoria
from households.models import Vivienda, Invitacion


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


class EditCategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = ('is_shared', 'is_shared_on_leave', 'hidden')
        labels = {
            'is_shared': 'Compartida',
            'is_shared_on_leave': 'Compartida en Vacación',
            'hidden': 'Oculta'
        }

    def clean(self):
        cleaned_data = super(EditCategoriaForm, self).clean()
        is_shared = cleaned_data.get("is_shared")
        is_shared_on_leave = cleaned_data.get("is_shared_on_leave")
        if not is_shared and is_shared_on_leave:
            raise forms.ValidationError(
                "Si la categoría no es compartida, no puede ser marcada como "
                "compartida en vacación."
            )


class ItemForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = ("nombre", "unidad_medida", "descripcion")


class ItemListaForm(forms.ModelForm):

    class Meta:
        model = ItemLista
        fields = ('item', 'cantidad_solicitada')


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


class BaseItemListaFormSet(forms.models.BaseInlineFormSet):

    def __init__(self, valid_items_queryset, *args, **kwargs):
        super(BaseItemListaFormSet, self).__init__(*args, **kwargs)

        self.valid_items_queryset = valid_items_queryset

        for form in self.forms:
            form.fields['item'].queryset = valid_items_queryset

    @property
    def empty_form(self):
        form = self.form(
            auto_id=self.auto_id,
            prefix=self.add_prefix('__prefix__'),
            empty_permitted=True,
            **self.get_form_kwargs(None)
        )
        self.add_fields(form, None)
        form.fields['item'].queryset = self.valid_items_queryset
        return form
