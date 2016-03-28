# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Vivienda(models.Model):
	alias = models.CharField(max_length=200)
	def __unicode__(self):
		return self.alias

class ViviendaUsuario(models.Model):
	class Meta:
		unique_together = (('vivienda', 'user'),)
	vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)

	def __unicode__(self):
		return str(self.vivienda) + "__" + str(self.user)

class Invitacion(models.Model):
	# this key can be null if you invite an account-less user. In this case the invitation is sent to the email.
	invitado = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
	invitado_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	email = models.EmailField()
	def __unicode__(self):
		return str(self.invitado) + "__invited__" + str(self.invitado_por)

class SolicitudAbandonarVivienda(models.Model):
	creada_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	fecha = models.DateField()
	estado = models.CharField(max_length=100)
	def __unicode__(self):
		return str(self.creada_por) + "__" + str(self.fecha)

class Categoria(models.Model):
	nombre = models.CharField(max_length=100, primary_key=True)
	def __unicode__(self):
		return self.nombre

class Item(models.Model):
	nombre = models.CharField(max_length=255)
	descripcion = models.CharField(max_length=255)
	def __unicode__(self):
		return self.nombre

class YearMonth(models.Model):
	class Meta:
		unique_together = (('year', 'month'),)

	year = models.IntegerField()
	month = models.IntegerField()
	def __unicode__(self):
		return str(self.year) + "__" + str(self.month)

class Presupuesto(models.Model):
	class Meta:
		unique_together = (('categoria', 'vivienda', 'year_month'),)

	categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
	vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
	year_month = models.ForeignKey(YearMonth, on_delete=models.CASCADE)
	def __unicode__(self):
		return "".join((str(self.vivienda), "__", str(self.categoria), "__", str(self.year_month)))

class ListaCompras(models.Model):
	usuario_creacion = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	fecha = models.DateField()
	estado = models.CharField(max_length=255)
	def __unicode__(self):
		return "".join((str(self.usuario_creacion), "__", str(self.fecha), "__", str(self.estado)))

class ItemLista(models.Model):
	class Meta:
		unique_together = (('item', 'lista'),)

	item = models.ForeignKey(Item, on_delete=models.CASCADE)
	lista = models.ForeignKey(ListaCompras, on_delete=models.CASCADE)
	cantidad_solicitada = models.IntegerField()
	cantidad_comprada = models.IntegerField()
	estado = models.CharField(max_length=255)
	def __unicode__(self):
		return str(self.item) + "__" + str(self.lista)

class Gasto(models.Model):
	monto = models.IntegerField()
	usuario = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE, null=True)
	categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
	fecha_creacion = models.DateField()
	fecha_pago = models.DateField(null=True)
	year_month = models.ForeignKey(YearMonth, on_delete=models.CASCADE, null=True)
	lista_compras = models.ForeignKey(ListaCompras, on_delete=models.CASCADE, blank=True, null=True)
	estado = models.CharField(max_length=255)
	def __unicode__(self):
		return "".join((str(self.usuario), "__", str(self.categoria), "__", str(self.year_month)))