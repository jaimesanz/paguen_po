# -*- coding: utf-8 -*-
from django import forms

from groceries.models import Item, ItemLista


class ItemForm(forms.ModelForm):

    class Meta:
        model = Item
        fields = ("nombre", "unidad_medida", "descripcion")


class ItemListaForm(forms.ModelForm):

    class Meta:
        model = ItemLista
        fields = ('item', 'cantidad_solicitada')


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