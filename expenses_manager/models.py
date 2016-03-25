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
		return self.vivienda + "__" + self.user

class Invitacion(models.Model):
	# this key can be null if you invite an account-less user. In this case the invitation is sent to the email.
	invitado = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
	invitado_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	email = models.EmailField()

	def __unicode__(self):
		return self.invitado + "__invited__" + self.invitado_por

class SolicitudAbandonarVivienda(models.Model):
	creada_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	fecha = models.DateField()
	estado = models.CharField(max_length=100)

	def __unicode__(self):
		return creada_por + "__" + self.fecha

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
		return self.year + "__" + self.month

class Presupuesto(models.Model):
	class Meta:
		unique_together = (('categoria', 'vivienda', 'year_month'),)
	categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
	vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
	year_month = models.ForeignKey(YearMonth, on_delete=models.CASCADE)

	def __unicode__(self):
		return "".join((self.vivienda, "__", self.categoria, "__", self.year_month))

class ListaCompras(models.Model):
	usuario_creacion = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	fecha = models.DateField()
	estado = models.CharField(max_length=255)

	def __unicode__(self):
		return "".join((self.usuario_creacion, "__", self.fecha, "__", self.estado))







