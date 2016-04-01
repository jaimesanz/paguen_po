# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


# proxy user. This is used to add methods to the User class without altering the default django
class ProxyUser(User):
	class Meta:
		proxy = True

	# returns the user's current active vivienda, or None
	def get_vu(self):
		return ViviendaUsuario.objects.filter(user=self, estado="activo").first()

	# returns a boolean value indicating if the user has an active vivienda
	def has_vivienda(self):
		return self.get_vu() is not None

	# returns the vivienda of the user, or None
	def get_vivienda(self):
		vivienda_usuario = self.get_vu()
		if vivienda_usuario is not None:
			return vivienda_usuario.vivienda
		else:
			return None

	# return a list of all active members of the Vivienda, including the User that calls the method
	# if there's no active vivienda, returns None
	def get_roommates(self):
		if self.has_vivienda():
			return ViviendaUsuario.objects.filter(vivienda=self.get_vivienda(), estado="activo")
		else:
			return None

	# returns pending invites related to the user (received and sent invites)
	def get_invites(self):
		invites_in = Invitacion.objects.filter(invitado=self, estado="pendiente")
		invites_out = Invitacion.objects.filter(invitado_por__user=self, estado="pendiente")
		return invites_in,invites_out

class Vivienda(models.Model):
	alias = models.CharField(max_length=200)
	def __unicode__(self):
		return self.alias

class ViviendaUsuario(models.Model):
	class Meta:
		unique_together = (('vivienda', 'user', 'estado', 'fecha_creacion'),)
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
		self.save()
		return ViviendaUsuario(user=self.invitado, vivienda=self.invitado_por.vivienda)
	def reject(self):
		self.estado = "rechazada"
		self.save()
	def cancel(self):
		self.estado = "cancelada"
		self.save()

	# return True if the given user is the one that's beign invited
	def is_invited_user(self, user):
		return self.invitado == user
	# returns True if the given user is the one sendnf the invitation
	def is_invited_by_user(self, user):
		return self.invitado_por.user == user

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