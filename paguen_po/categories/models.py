# -*- coding: utf-8 -*-
from django.db import models


def get_default_others_categoria():
    """
    Returns the default Categoria for "Other" Gasto instances. Gastos
    with a hidden Categoria are shown as if they belonged to this Categoria
    :return: Categoria
    """
    return Categoria.objects.get_or_create(nombre="Otros", vivienda=None)[0]


class Categoria(models.Model):

    class Meta:
        ordering = ['nombre']
        unique_together = (('nombre', 'vivienda'),)
    nombre = models.CharField(max_length=100)
    vivienda = models.ForeignKey(
        "households.Vivienda",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None)
    hidden = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=True)
    is_shared_on_leave = models.BooleanField(default=True)
    is_transfer = models.BooleanField(default=False)

    def is_global(self):
        """
        Returns True if the Categoria is Global and shared with every Vivienda
        :return: Boolean
        """
        return Categoria.objects.filter(
            vivienda=None,
            nombre=self.nombre).exists()

    def is_hidden(self):
        """
        Returns it's hidden field's boolean value
        :return: Boolean
        """
        return self.hidden

    def hide(self):
        """
        If the Categoria is not hidden, changes this Categoria's hidden
        field to True and returns True. If it's already hidden, returns
        False and does nothing
        :return: Boolean
        """
        if not self.is_hidden():
            self.hidden = True
            self.save()
            return True
        return False

    def show(self):
        """
        If this Categoria is not hidden, it returns False. If it's
        hidden, changes the it's hidden field to False
        :return: Boolean
        """
        if self.is_hidden():
            self.hidden = False
            self.save()
            return True
        return False

    def toggle(self):
        """
        Toggles the hidden field of this Categoria.
        :return: Boolean
        """
        if self.is_hidden():
            return self.show()
        return self.hide()

    def __str__(self):
        return self.nombre
