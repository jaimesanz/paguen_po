# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


# proxy user. This is used to add methods to the User class without altering the default django
class ProxyUser(User):
	class Meta:
		proxy = True
	def has_vivienda(self):
		return len(ViviendaUsuario.objects.filter(user=self))>0

class Vivienda(models.Model):
	alias = models.CharField(max_length=200)
	def __unicode__(self):
		return self.alias

class ViviendaUsuario(models.Model):
	class Meta:
		unique_together = (('vivienda', 'user', 'fecha_creacion'),)
	vivienda = models.ForeignKey(Vivienda, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	estado = models.CharField(max_length=200, default="activo")
	fecha_creacion = models.DateTimeField(auto_now_add=True)
	def leave(self):
		self.estado = "inactivo"
		self.save()
	def is_active(self):
		return self.estado == "activo"
	def __unicode__(self):
		return str(self.vivienda) + "__" + str(self.user)

class Invitacion(models.Model):
	# this key can be null if you invite an account-less user. In this case the invitation is sent to the email.
	invitado = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
	invitado_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	email = models.EmailField()
	estado = models.CharField(max_length=200, default="pendiente")
	# estado es pendiente, rechazada o aceptada
	def __unicode__(self):
		return str(self.invitado_por) + "__invited__" + str(self.invitado)
	def accept(self):
		self.estado = "aceptada"
		return ViviendaUsuario(user=self.invitado, vivienda=self.invitado_por.vivienda)
	def reject(self):
		self.estado = "rechazada"
	def cancel(self):
		self.estado = "cancelada"

class SolicitudAbandonarVivienda(models.Model):
	creada_por = models.ForeignKey(ViviendaUsuario, on_delete=models.CASCADE)
	fecha = models.DateTimeField(auto_now_add=True)
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
	fecha_creacion = models.DateTimeField(auto_now_add=True)
	fecha_pago = models.DateTimeField(null=True)
	year_month = models.ForeignKey(YearMonth, on_delete=models.CASCADE, null=True)
	lista_compras = models.ForeignKey(ListaCompras, on_delete=models.CASCADE, blank=True, null=True)
	estado = models.CharField(max_length=255)
	def __unicode__(self):
		return "".join((str(self.usuario), "__", str(self.categoria), "__", str(self.year_month)))