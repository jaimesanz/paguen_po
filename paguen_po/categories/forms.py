# -*- coding: utf-8 -*-
from django import forms

from categories.models import Categoria


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
